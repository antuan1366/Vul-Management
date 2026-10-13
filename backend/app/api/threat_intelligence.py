import asyncio
import json
import os
import re
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.feed import Feed
from app.models.threat_intelligence import (
    TelegramFeed,
    TelegramScanResult,
    TelegramScanRun,
    ThreatIntelligence,
)
from app.schemas.threat_intelligence import (
    IntelligenceUpdate,
    ReviewRequest,
    TelegramFeedCreate,
    TelegramFeedUpdate,
    TelegramScanRequest,
)
from app.services.threat_intelligence import (
    collect_telegram_scan,
    enrich_scan_result_from_nvd,
    serialize_feed,
    serialize_intelligence,
    serialize_scan_result,
    serialize_scan_run,
    send_jira_ticket,
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


@router.get("/scan-runs")
def list_scan_runs(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    items = db.scalars(select(TelegramScanRun).order_by(TelegramScanRun.created_at.desc()).limit(limit)).all()
    return {"items": [serialize_scan_run(item) for item in items], "total": len(items)}


@router.get("/scan-runs/{run_id}")
def get_scan_run(run_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanRun, run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan run not found.")
    return serialize_scan_run(item)


@router.get("/scan-results")
def list_scan_results(
    status: str = "all",
    q: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = select(TelegramScanResult).order_by(TelegramScanResult.date.desc()).limit(limit)
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


@router.post("/scan-results/{result_id}/review")
def review_scan_result(result_id: int, data: ReviewRequest, db: Session = Depends(get_db)):
    if data.status not in {"under_review", "rejected"}:
        raise HTTPException(status_code=400, detail="Review status must be under_review or rejected.")
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    if item.review_status == "approved":
        raise HTTPException(status_code=409, detail="This CVE is already approved into Intelligence.")
    item.review_status = data.status
    item.review_notes = data.notes
    item.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return serialize_scan_result(item)


@router.post("/scan-results/{result_id}/enrich")
def enrich_scan_result(result_id: int, db: Session = Depends(get_db)):
    item = db.get(TelegramScanResult, result_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Scan result not found.")
    if item.review_status == "rejected":
        raise HTTPException(status_code=409, detail="Rejected results cannot be enriched.")
    try:
        enrich_scan_result_from_nvd(db, item)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except (httpx.HTTPError, ValueError) as error:
        item.nvd_status = "error"
        item.nvd_error = f"NVD request failed: {error.__class__.__name__}."
        db.commit()
        raise HTTPException(status_code=502, detail=item.nvd_error)
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
        return {"status": "already_exists", "intelligence_id": existing.id, "cve_id": existing.cve_id}
    record = ThreatIntelligence(
        cve_id=item.cve_id,
        severity=item.severity,
        cvss_score=item.cvss_score,
        affected_product=item.affected_product,
        affected_versions=item.affected_versions,
        remediation=item.remediation,
        mitigation=item.mitigation,
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
    return {"status": "approved", "intelligence_id": record.id, "cve_id": record.cve_id}


@router.get("/intelligence")
def list_intelligence(q: str | None = None, limit: int = Query(default=200, ge=1, le=500), db: Session = Depends(get_db)):
    query = select(ThreatIntelligence).order_by(ThreatIntelligence.date.desc()).limit(limit)
    if q:
        needle = f"%{q.strip()}%"
        query = query.where(
            ThreatIntelligence.cve_id.ilike(needle)
            | ThreatIntelligence.affected_product.ilike(needle)
        )
    items = db.scalars(query).all()
    return {"items": [serialize_intelligence(item) for item in items], "total": len(items)}


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
        raise HTTPException(status_code=502, detail=f"Jira request failed: {error.__class__.__name__}.")
    item.jira_issue_key = result["key"]
    item.jira_issue_url = result["url"]
    item.jira_status = "sent"
    item.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "sent", "issue_key": item.jira_issue_key, "issue_url": item.jira_issue_url}
