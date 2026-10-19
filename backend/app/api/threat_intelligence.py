import asyncio
import json
import os
import re
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.services.application_events import record_event, exception_details
from app.models.feed import Feed
from app.models.threat_intelligence import (
    TelegramFeed,
    TelegramScanResult,
    TelegramScanRun,
    TelegramScanSchedule,
    ThreatIntelligence,
)
from app.schemas.threat_intelligence import (
    IntelligenceCreate,
    IntelligenceUpdate,
    ReviewRequest,
    TelegramFeedCreate,
    TelegramFeedUpdate,
    TelegramScanRequest,
    TelegramScheduleUpdate,
)
from app.services.threat_intelligence import (
    collect_telegram_scan,
    enrich_scan_result_from_sources,
    serialize_feed,
    serialize_intelligence,
    serialize_scan_result,
    serialize_scan_run,
    send_jira_ticket,
    telegram_scheduler_loop,
)

router = APIRouter(prefix="/api/threat-intelligence", tags=["Threat Intelligence"])
CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)


@router.get("/feeds")
def list_telegram_feeds(db: Session = Depends(get_db)):
    items = db.scalars(select(TelegramFeed).order_by(TelegramFeed.name)).all()
    return {"items": [serialize_feed(item) for item in items], "total": len(items)}


@router.post("/feeds", status_code=201)
def create_telegram_feed(data: TelegramFeedCreate, db: Session = Depends(get_db)):
    username = data.channel_username.strip().lstrip("@").rstrip("/")
    username = username.split("/")[-1]
    if not re.fullmatch(r"[A-Za-z0-9_]{5,150}", username):
        raise HTTPException(status_code=400, detail="Enter a public Telegram channel username, with or without @.")
    existing = db.scalar(select(TelegramFeed).where(TelegramFeed.channel_username == username))
    if existing:
        raise HTTPException(status_code=409, detail="This Telegram channel is already configured.")
    item = TelegramFeed(name=data.name.strip(), channel_username=username, enabled=data.enabled)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_feed(item)


@router.put("/feeds/{feed_id}")
def update_telegram_feed(feed_id: int, data: TelegramFeedUpdate, db: Session = Depends(get_db)):
    item = db.get(TelegramFeed, feed_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Telegram feed not found.")
    values = data.model_dump(exclude_unset=True)
    if "channel_username" in values and values["channel_username"] is not None:
        username = values["channel_username"].strip().lstrip("@").rstrip("/").split("/")[-1]
        if not re.fullmatch(r"[A-Za-z0-9_]{5,150}", username):
            raise HTTPException(status_code=400, detail="Enter a public Telegram channel username.")
        duplicate = db.scalar(select(TelegramFeed).where(
            TelegramFeed.channel_username == username, TelegramFeed.id != feed_id
        ))
        if duplicate:
            raise HTTPException(status_code=409, detail="This Telegram channel is already configured.")
        values["channel_username"] = username
    for key, value in values.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return serialize_feed(item)


@router.delete("/feeds/{feed_id}", status_code=204)
def delete_telegram_feed(feed_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramFeed, feed_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Telegram feed not found.")
    db.delete(item)
    db.commit()


@router.post("/scan", status_code=202)
async def start_telegram_scan(data: TelegramScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if data.mode not in {"new", "from_date"}:
        raise HTTPException(status_code=400, detail="mode must be 'new' or 'from_date'.")
    if data.mode == "from_date" and data.start_date is None:
        raise HTTPException(status_code=400, detail="start_date is required for historical scans.")
    feeds = db.scalars(select(TelegramFeed).where(TelegramFeed.enabled.is_(True))).all()
    if not feeds:
        raise HTTPException(status_code=400, detail="Add and enable at least one Telegram channel before scanning.")
    run = TelegramScanRun(
        mode=data.mode,
        start_date=data.start_date,
        status="pending",
        channels_total=len(feeds),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(collect_telegram_scan, run.id)
    return {"scan_run_id": run.id, "status": run.status, "channels_total": run.channels_total}




@router.get("/schedule")
def get_telegram_schedule(db: Session = Depends(get_db)):
    item = db.scalar(select(TelegramScanSchedule).order_by(TelegramScanSchedule.id))
    if item is None:
        item = TelegramScanSchedule(enabled=False, frequency="daily", scan_time="02:00", day_of_week=0)
        db.add(item)
        db.commit()
        db.refresh(item)
    return {
        "enabled": item.enabled,
        "frequency": item.frequency,
        "scan_time": item.scan_time,
        "day_of_week": item.day_of_week,
        "last_run_date": item.last_run_date,
    }


@router.put("/schedule")
def update_telegram_schedule(data: TelegramScheduleUpdate, db: Session = Depends(get_db)):
    if data.frequency not in {"daily", "weekly"}:
        raise HTTPException(status_code=400, detail="frequency must be daily or weekly.")
    item = db.scalar(select(TelegramScanSchedule).order_by(TelegramScanSchedule.id))
    if item is None:
        item = TelegramScanSchedule()
        db.add(item)
    item.enabled = data.enabled
    item.frequency = data.frequency
    item.scan_time = data.scan_time
    item.day_of_week = data.day_of_week
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return {
        "enabled": item.enabled,
        "frequency": item.frequency,
        "scan_time": item.scan_time,
        "day_of_week": item.day_of_week,
        "last_run_date": item.last_run_date,
    }


def _scan_run_progress(db: Session, item: TelegramScanRun) -> dict:
    # NVD is keyed by CVE ID, so progress counts unique CVEs rather than Telegram occurrences.
    rows = db.execute(
        select(TelegramScanResult.cve_id, TelegramScanResult.nvd_status).where(
            TelegramScanResult.scan_run_id == item.id
        )
    ).all()
    by_cve: dict[str, list[str]] = {}
    for cve_id, nvd_status in rows:
        by_cve.setdefault(cve_id, []).append(nvd_status)
    processed_statuses = {"success", "partial", "not_found", "error", "skipped"}
    result_total = len(by_cve)
    result_processed = sum(
        1 for statuses in by_cve.values()
        if statuses and all(status in processed_statuses for status in statuses)
    )
    remaining = max(0, result_total - result_processed)
    github_feed = db.scalar(
        select(Feed).where(Feed.feed_type == "github_advisory", Feed.enabled.is_(True)).order_by(Feed.id)
    )
    nvd_feed = db.scalar(
        select(Feed).where(Feed.feed_type == "nvd_cve", Feed.enabled.is_(True)).order_by(Feed.id)
    )
    # Conservative estimate: anonymous GitHub can add about 62 seconds per CVE
    # only when the NVD/CVE Program records leave core fields missing.
    estimated_seconds_per_cve = (
        62 if github_feed and not github_feed.api_key
        else 2.5 if nvd_feed and nvd_feed.api_key
        else 7
    )
    return {
        **serialize_scan_run(item),
        "nvd_total": result_total,
        "nvd_processed": result_processed,
        "nvd_remaining": remaining,
        "nvd_estimated_seconds": remaining * estimated_seconds_per_cve if item.status == "nvd_scanning" else 0,
    }


@router.get("/scan-runs")
def list_scan_runs(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    items = db.scalars(select(TelegramScanRun).order_by(TelegramScanRun.created_at.desc()).limit(limit)).all()
    return {"items": [_scan_run_progress(db, item) for item in items], "total": len(items)}


@router.get("/scan-runs/{run_id}")
def get_scan_run(run_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanRun, run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan run not found.")
    return _scan_run_progress(db, item)


@router.get("/scan-results")
def list_scan_results(
    status: str = "all",
    q: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    run_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(TelegramScanResult).order_by(TelegramScanResult.cve_id.asc(), TelegramScanResult.id.asc()).limit(limit)
    if run_id is not None:
        query = query.where(TelegramScanResult.scan_run_id == run_id)
    if status != "all":
        query = query.where(TelegramScanResult.review_status == status)
    if q:
        needle = f"%{q.strip()}%"
        query = query.where(
            TelegramScanResult.cve_id.ilike(needle)
            | TelegramScanResult.channel_name.ilike(needle)
            | TelegramScanResult.message_text.ilike(needle)
        )
    items = db.scalars(query).all()
    return {"items": [serialize_scan_result(item) for item in items], "total": len(items)}


@router.get("/scan-results/{result_id}")
def get_scan_result(result_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    return serialize_scan_result(item)


@router.delete("/scan-results/{result_id}", status_code=204)
def delete_scan_result(result_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")

    # Keep accepted findings while their Vulnerabilities Register record exists.
    # If that register record was deleted, the accepted scan result can also be removed.
    if item.review_status == "approved":
        linked_vulnerability = db.scalar(
            select(ThreatIntelligence).where(ThreatIntelligence.cve_id == item.cve_id)
        )
        if linked_vulnerability is not None:
            raise HTTPException(
                status_code=409,
                detail="Delete this CVE from Vulnerabilities before deleting its accepted Scan Result."
            )

    deleted_cve = item.cve_id
    run_id = item.scan_run_id
    db.delete(item)
    db.commit()
    record_event("WARNING", "audit", "Scan Result", "finding_deleted",
                 f"Scan result for {deleted_cve} was deleted.",
                 cve_id=deleted_cve, scan_run_id=run_id)


@router.post("/scan-results/{result_id}/review")
def review_scan_result(result_id: int, data: ReviewRequest, db: Session = Depends(get_db)):
    if data.status not in {"new", "under_review", "rejected"}:
        raise HTTPException(status_code=400, detail="Review status must be new, under_review, or rejected.")
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    if item.review_status == "approved":
        raise HTTPException(status_code=409, detail="Accepted results cannot be moved back to review.")
    item.review_status = data.status
    item.review_notes = data.notes
    item.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    record_event("INFO" if item.review_status != "rejected" else "WARNING",
                 "audit", "Scan Result review", "review_status_changed",
                 f"{item.cve_id} review status changed to {item.review_status}.",
                 cve_id=item.cve_id, scan_run_id=item.scan_run_id,
                 details={"review_notes": item.review_notes})
    return serialize_scan_result(item)


@router.post("/scan-results/{result_id}/enrich")
def enrich_scan_result(result_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    if item.review_status == "rejected":
        raise HTTPException(status_code=409, detail="Rejected results cannot be enriched.")
    try:
        enrich_scan_result_from_sources(db, item)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except (httpx.HTTPError, ValueError) as error:
        item.nvd_status = "error"
        item.nvd_error = f"NVD request failed: {error.__class__.__name__}."
        db.commit()
        raise HTTPException(status_code=502, detail=item.nvd_error)
    db.refresh(item)
    return serialize_scan_result(item)




@router.put("/scan-results/{result_id}")
def update_scan_result(result_id: int, data: IntelligenceUpdate, db: Session = Depends(get_db)):
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    if item.review_status == "rejected":
        raise HTTPException(status_code=409, detail="Rejected scan results cannot be edited.")
    values = data.model_dump(exclude_unset=True)
    mapping = {
        "severity": "severity",
        "cvss_score": "cvss_score",
        "affected_product": "affected_product",
        "affected_versions": "affected_versions",
        "description": "nvd_description",
        "references_text": "references_text",
    }
    for key, value in values.items():
        setattr(item, mapping[key], value)
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return serialize_scan_result(item)


@router.post("/scan-results/{result_id}/approve", status_code=201)
def approve_scan_result(result_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    existing = db.scalar(select(ThreatIntelligence).where(ThreatIntelligence.cve_id == item.cve_id))
    if existing:
        item.review_status = "approved"
        item.reviewed_at = datetime.utcnow()
        db.commit()
        record_event("INFO", "audit", "Threat Intelligence", "cve_approved_existing",
                     f"{item.cve_id} was accepted; a Vulnerabilities record already existed.",
                     cve_id=item.cve_id, scan_run_id=item.scan_run_id)
        return {"status": "already_exists", "intelligence_id": existing.id, "cve_id": existing.cve_id}
    record = ThreatIntelligence(
        cve_id=item.cve_id,
        severity=item.severity,
        cvss_score=item.cvss_score,
        affected_product=item.affected_product,
        affected_versions=item.affected_versions,
        # Remediation and mitigation are deliberately left for the administrator
        # to define in the Vulnerability Register after accepting the finding.
        description=item.nvd_description or item.message_text,
        references_text=item.references_text,
        nvd_url=f"https://nvd.nist.gov/vuln/detail/{item.cve_id}",
        source_message=item.message_text,
        source_channel=item.channel_username,
        date=item.date,
    )
    db.add(record)
    item.review_status = "approved"
    item.reviewed_at = datetime.utcnow()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This CVE was approved by another request.")
    db.refresh(record)
    record_event("INFO", "audit", "Threat Intelligence", "cve_approved",
                 f"{item.cve_id} was accepted into Vulnerabilities.",
                 cve_id=item.cve_id, scan_run_id=item.scan_run_id,
                 details={"intelligence_id": record.id})
    return {"status": "approved", "intelligence_id": record.id, "cve_id": record.cve_id}


@router.get("/intelligence")
def list_intelligence(q: str | None = None, limit: int = Query(default=200, ge=1, le=500), db: Session = Depends(get_db)):
    query = select(ThreatIntelligence).order_by(ThreatIntelligence.date.desc(), ThreatIntelligence.id.desc()).limit(limit)
    if q:
        needle = f"%{q.strip()}%"
        query = query.where(
            ThreatIntelligence.cve_id.ilike(needle)
            | ThreatIntelligence.affected_product.ilike(needle)
        )
    items = db.scalars(query).all()
    return {"items": [serialize_intelligence(item) for item in items], "total": len(items)}


@router.post("/intelligence", status_code=201)
def create_intelligence(data: IntelligenceCreate, db: Session = Depends(get_db)):
    cve_id = data.cve_id.strip().upper()
    if not CVE_PATTERN.fullmatch(cve_id):
        raise HTTPException(status_code=422, detail="Enter a valid CVE ID, for example CVE-2025-12345.")
    existing = db.scalar(select(ThreatIntelligence).where(ThreatIntelligence.cve_id == cve_id))
    if existing:
        raise HTTPException(status_code=409, detail="This CVE already exists in Vulnerabilities.")
    values = data.model_dump(exclude={"cve_id"})
    item = ThreatIntelligence(
        cve_id=cve_id,
        severity=values.get("severity"),
        cvss_score=values.get("cvss_score"),
        affected_product=values.get("affected_product"),
        affected_versions=values.get("affected_versions"),
        remediation=values.get("remediation"),
        mitigation=values.get("mitigation"),
        description=values.get("description"),
        references_text=values.get("references_text"),
        nvd_url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
        source_message="Manually added by administrator",
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This CVE already exists in Vulnerabilities.")
    db.refresh(item)
    return serialize_intelligence(item)


@router.get("/intelligence/{record_id}")
def get_intelligence(record_id: int, db: Session = Depends(get_db)):
    item = db.get(ThreatIntelligence, record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Intelligence record not found.")
    return serialize_intelligence(item)


@router.put("/intelligence/{record_id}")
def update_intelligence(record_id: int, data: IntelligenceUpdate, db: Session = Depends(get_db)):
    item = db.get(ThreatIntelligence, record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Intelligence record not found.")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return serialize_intelligence(item)


@router.delete("/intelligence/{record_id}", status_code=204)
def delete_intelligence(record_id: int, db: Session = Depends(get_db)):
    item = db.get(ThreatIntelligence, record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Intelligence record not found.")

    cve_id = item.cve_id
    jira_issue_key = item.jira_issue_key
    db.delete(item)
    db.commit()
    record_event(
        "WARNING",
        "audit",
        "Vulnerability Register",
        "vulnerability_deleted",
        f"{cve_id} was deleted from the Vulnerability Register.",
        cve_id=cve_id,
        details={"jira_issue_key": jira_issue_key},
    )


@router.post("/intelligence/{record_id}/jira")
def create_jira_ticket(record_id: int, db: Session = Depends(get_db)):
    item = db.get(ThreatIntelligence, record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Intelligence record not found.")
    if item.jira_issue_key and item.jira_issue_url:
        return {"status": "already_sent", "issue_key": item.jira_issue_key, "issue_url": item.jira_issue_url}
    try:
        result = send_jira_ticket(item)
    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except httpx.HTTPError as error:
        record_event("ERROR", "integration", "Jira", "jira_request_failed",
                     f"Jira request failed: {error.__class__.__name__}: {str(error)[:500]}",
                     cve_id=item.cve_id, details=exception_details(error))
        raise HTTPException(status_code=502, detail=f"Jira request failed: {error.__class__.__name__}.")
    item.jira_issue_key = result["key"]
    item.jira_issue_url = result["url"]
    item.jira_status = "sent"
    item.updated_at = datetime.utcnow()
    db.commit()
    record_event("INFO", "integration", "Jira", "jira_ticket_created",
                 f"Jira issue {item.jira_issue_key} created for {item.cve_id}.",
                 cve_id=item.cve_id, details={"issue_key": item.jira_issue_key})
    return {"status": "sent", "issue_key": item.jira_issue_key, "issue_url": item.jira_issue_url}
