import asyncio
import json
import os
import re
from datetime import datetime, time
from pathlib import Path
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.core.config import settings
from app.models.feed import Feed
from app.models.threat_intelligence import TelegramFeed, TelegramScanResult, TelegramScanRun, TelegramScanSchedule, ThreatIntelligence

CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)


def serialize_feed(item: TelegramFeed) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "channel_username": item.channel_username,
        "enabled": item.enabled,
        "last_message_id": item.last_message_id,
        "created_at": item.created_at,
    }


def serialize_scan_run(item: TelegramScanRun) -> dict:
    return {
        "id": item.id,
        "mode": item.mode,
        "start_date": item.start_date,
        "status": item.status,
        "channels_total": item.channels_total,
        "channels_processed": item.channels_processed,
        "messages_processed": item.messages_processed,
        "cve_occurrences": item.cve_occurrences,
        "error_message": item.error_message,
        "started_at": item.started_at,
        "finished_at": item.finished_at,
        "date": item.created_at,
    }


def serialize_scan_result(item: TelegramScanResult) -> dict:
    return {
        "id": item.id,
        "scan_run_id": item.scan_run_id,
        "cve_id": item.cve_id,
        "channel_name": item.channel_name,
        "channel_username": item.channel_username,
        "telegram_message_id": item.telegram_message_id,
        "message_text": item.message_text,
        "message_summary": " ".join(item.message_text.split())[:180],
        "message_url": item.message_url,
        "date": item.date,
        "last_seen_at": item.last_seen_at,
        "scan_count": item.scan_count,
        "review_status": item.review_status,
        "nvd_status": item.nvd_status,
        "nvd_error": item.nvd_error,
        "severity": item.severity,
        "cvss_score": item.cvss_score,
        "affected_product": item.affected_product,
        "affected_versions": item.affected_versions,
        "remediation": item.remediation,
        "mitigation": item.mitigation,
        "nvd_description": item.nvd_description,
        "references_text": item.references_text,
        "nvd_missing_fields": item.nvd_missing_fields,
        "review_notes": item.review_notes,
        "reviewed_at": item.reviewed_at,
    }


def serialize_intelligence(item: ThreatIntelligence) -> dict:
    return {
        "id": item.id,
        "cve_id": item.cve_id,
        "severity": item.severity,
        "cvss_score": item.cvss_score,
        "affected_product": item.affected_product,
        "affected_versions": item.affected_versions,
        "remediation": item.remediation,
        "mitigation": item.mitigation,
        "description": item.description,
        "references_text": item.references_text,
        "nvd_url": item.nvd_url,
        "source_message": item.source_message,
        "source_channel": item.source_channel,
        "date": item.date,
        "jira_issue_key": item.jira_issue_key,
        "jira_issue_url": item.jira_issue_url,
        "jira_status": item.jira_status,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _get_telegram_client():
    api_id = settings.telegram_api_id
    api_hash = settings.telegram_api_hash
    session_path = settings.telegram_session
    if not api_id or not api_hash:
        raise RuntimeError("Telegram is not configured. Set TELEGRAM_API_ID and TELEGRAM_API_HASH, then run backend/scripts/login_telegram.py once.")
    try:
        from telethon import TelegramClient
    except ImportError as error:
        raise RuntimeError("Telethon is not installed. Install the project requirements first.") from error
    session_file = Path(session_path)
    if not session_file.is_absolute():
        session_file = Path(__file__).resolve().parents[2] / session_file
    session_file.parent.mkdir(parents=True, exist_ok=True)
    return TelegramClient(str(session_file), int(api_id), api_hash)


async def collect_telegram_scan(run_id: int) -> None:
    db = SessionLocal()
    run = db.get(TelegramScanRun, run_id)
    if run is None:
        db.close()
        return
    run.status = "running"
    run.started_at = datetime.utcnow()
    db.commit()
    try:
        client = _get_telegram_client()
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session is not authorized. Run backend/scripts/login_telegram.py from the backend directory.")
        feeds = db.scalars(select(TelegramFeed).where(TelegramFeed.enabled.is_(True)).order_by(TelegramFeed.id)).all()
        run.channels_total = len(feeds)
        db.commit()
        for feed in feeds:
            try:
                entity = await client.get_entity(feed.channel_username)
                max_message_id = feed.last_message_id or 0
                if run.mode == "from_date":
                    messages = client.iter_messages(entity, reverse=True, offset_date=run.start_date)
                elif feed.last_message_id:
                    messages = client.iter_messages(entity, min_id=feed.last_message_id, reverse=True)
                else:
                    # Initial discovery is bounded to the latest 200 messages.
                    messages = client.iter_messages(entity, limit=200)
                async for message in messages:
                    if not message or not getattr(message, "message", None):
                        continue
                    text = message.message
                    cves = sorted(set(match.upper() for match in CVE_PATTERN.findall(text)))
                    run.messages_processed += 1
                    max_message_id = max(max_message_id, int(message.id))
                    if not cves:
                        continue
                    message_url = f"https://t.me/{feed.channel_username}/{message.id}"
                    for cve_id in cves:
                        existing = db.scalar(select(TelegramScanResult).where(
                            TelegramScanResult.channel_username == feed.channel_username,
                            TelegramScanResult.telegram_message_id == int(message.id),
                            TelegramScanResult.cve_id == cve_id,
                        ))
                        now = datetime.utcnow()
                        if existing:
                            existing.last_seen_at = now
                            existing.scan_count += 1
                            existing.scan_run_id = run.id
                        else:
                            result = TelegramScanResult(
                                scan_run_id=run.id,
                                cve_id=cve_id,
                                channel_name=feed.name,
                                channel_username=feed.channel_username,
                                telegram_message_id=int(message.id),
                                message_text=text,
                                message_url=message_url,
                                date=now,
                                last_seen_at=now,
                            )
                            db.add(result)
                        run.cve_occurrences += 1
                    db.commit()
                feed.last_message_id = max_message_id or feed.last_message_id
                run.channels_processed += 1
                db.commit()
            except Exception as error:
                run.error_message = (run.error_message + "\n" if run.error_message else "") + f"{feed.channel_username}: {error.__class__.__name__}: {str(error)[:250]}"
                db.commit()
        run.finished_at = datetime.utcnow()
        result_count = db.query(TelegramScanResult).filter(TelegramScanResult.scan_run_id == run.id).count()
        if result_count:
            run.status = "nvd_scanning"
        else:
            run.status = "completed_with_errors" if run.error_message else "completed"
        db.commit()
        completed_run_id = run.id
        await client.disconnect()
        if result_count:
            # NVD enrichment is a separate background phase; the scan response and UI remain usable.
            asyncio.create_task(enrich_scan_run_from_nvd(completed_run_id))
    except Exception as error:
        run.status = "failed"
        run.error_message = f"{error.__class__.__name__}: {str(error)[:500]}"
        run.finished_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


async def enrich_scan_run_from_nvd(run_id: int) -> None:
    """Enrich each finding in a scan run in the background with a conservative NVD request rate."""
    db = SessionLocal()
    try:
        run = db.get(TelegramScanRun, run_id)
        if run is None:
            return
        run.status = "nvd_scanning"
        result_ids = list(db.scalars(
            select(TelegramScanResult.id)
            .where(TelegramScanResult.scan_run_id == run_id)
            .order_by(TelegramScanResult.date.asc(), TelegramScanResult.id.asc())
        ).all())
        # Preserve prior successful lookups for duplicate findings, and retry only unfinished/errors.
        work_ids = []
        for result_id in result_ids:
            item = db.get(TelegramScanResult, result_id)
            if item and item.nvd_status not in {"success", "partial", "not_found"}:
                item.nvd_status = "queued"
                item.nvd_error = None
                work_ids.append(result_id)
        db.commit()
        db.close()

        for index, result_id in enumerate(work_ids):
            await asyncio.to_thread(_enrich_result_in_worker, result_id)
            # NVD's unauthenticated public API is rate-limited. Six seconds is a conservative
            # cadence (about five requests per 30 seconds); keep it even when an API key exists.
            if index < len(work_ids) - 1:
                await asyncio.sleep(6)

        db = SessionLocal()
        run = db.get(TelegramScanRun, run_id)
        if run:
            failures = db.query(TelegramScanResult).filter(
                TelegramScanResult.scan_run_id == run_id,
                TelegramScanResult.nvd_status == "error",
            ).count()
            run.status = "completed_with_errors" if run.error_message or failures else "completed"
            run.finished_at = datetime.utcnow()
            db.commit()
    except Exception as error:
        db = SessionLocal()
        try:
            run = db.get(TelegramScanRun, run_id)
            if run:
                run.status = "completed_with_errors"
                detail = f"NVD enrichment worker: {error.__class__.__name__}: {str(error)[:250]}"
                run.error_message = (run.error_message + "\\n" if run.error_message else "") + detail
                run.finished_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    finally:
        try:
            db.close()
        except Exception:
            pass


def _enrich_result_in_worker(result_id: int) -> None:
    """Use an isolated SQLAlchemy session so synchronous HTTP requests never block the event loop."""
    db = SessionLocal()
    try:
        item = db.get(TelegramScanResult, result_id)
        if item is None:
            return
        if item.review_status == "rejected":
            item.nvd_status = "skipped"
            item.nvd_error = "Skipped because the administrator rejected this finding."
            db.commit()
            return
        try:
            enrich_scan_result_from_nvd(db, item)
        except LookupError:
            # A not-found response is already saved as nvd_status=not_found.
            pass
        except (httpx.HTTPError, ValueError) as error:
            item.nvd_status = "error"
            item.nvd_error = f"NVD request failed: {error.__class__.__name__}."
            db.commit()
    finally:
        db.close()


def _walk_cpe_matches(node):
    if isinstance(node, dict):
        for match in node.get("cpeMatch", []) or []:
            criteria = match.get("criteria") or match.get("cpe23Uri")
            if criteria:
                parts = criteria.split(":")
                product = ":".join(parts[3:5]) if len(parts) >= 5 else criteria
                versions = []
                if match.get("versionStartIncluding"):
                    versions.append(f">= {match['versionStartIncluding']}")
                if match.get("versionStartExcluding"):
                    versions.append(f"> {match['versionStartExcluding']}")
                if match.get("versionEndIncluding"):
                    versions.append(f"<= {match['versionEndIncluding']}")
                if match.get("versionEndExcluding"):
                    versions.append(f"< {match['versionEndExcluding']}")
                if len(parts) > 5 and parts[5] not in {"*", "-"} and not versions:
                    versions.append(parts[5])
                yield product.replace(":", " "), ", ".join(versions) if versions else "Version range not specified"
        for value in node.values():
            if isinstance(value, (dict, list)):
                yield from _walk_cpe_matches(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_cpe_matches(value)


def enrich_scan_result_from_nvd(db, item: TelegramScanResult) -> None:
    # NVD's public API can be queried without a key. Use a configured key if one exists,
    # but do not require an Administration feed just to perform a public CVE lookup.
    feed = db.scalar(select(Feed).where(Feed.feed_type == "nvd_cve", Feed.enabled.is_(True)).order_by(Feed.id))
    headers = {"Accept": "application/json", "User-Agent": "Vul-Management/3.0.0"}
    if feed and feed.api_key:
        headers["apiKey"] = feed.api_key
    timeout = feed.timeout_seconds if feed else 20
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = None
        for attempt in range(5):
            response = client.get("https://services.nvd.nist.gov/rest/json/cves/2.0", params={"cveId": item.cve_id})
            if response.status_code not in {429, 503}:
                break
            if attempt == 4:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            try:
                wait_seconds = max(6, min(60, int(retry_after))) if retry_after else min(60, 15 * (2 ** attempt))
            except ValueError:
                wait_seconds = min(60, 15 * (2 ** attempt))
            response.close()
            import time as time_module
            time_module.sleep(wait_seconds)
        if response is None:
            raise httpx.RequestError("NVD returned no response.")
        if response.status_code == 404:
            item.nvd_status = "not_found"
            item.nvd_error = f"{item.cve_id}: requested CVE data was not found in NVD."
            db.commit()
            raise LookupError(item.nvd_error)
        response.raise_for_status()
        payload = response.json()
    vulnerabilities = payload.get("vulnerabilities") or []
    if not vulnerabilities:
        item.nvd_status = "not_found"
        item.nvd_error = f"{item.cve_id}: requested CVE data was not found in NVD."
        db.commit()
        raise LookupError(item.nvd_error)
    cve = vulnerabilities[0].get("cve") or {}
    descriptions = cve.get("descriptions") or []
    english = next((entry.get("value") for entry in descriptions if entry.get("lang") == "en" and entry.get("value")), None)
    metrics = cve.get("metrics") or {}
    severity = None
    score = None
    for metric_key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(metric_key) or []
        if entries:
            cvss = entries[0].get("cvssData") or {}
            score = cvss.get("baseScore")
            severity = cvss.get("baseSeverity") or entries[0].get("baseSeverity")
            if not severity and score is not None:
                severity = "CRITICAL" if score >= 9 else "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"
            break
    cpe_entries = list(_walk_cpe_matches(cve.get("configurations") or []))
    products = sorted(set(entry[0] for entry in cpe_entries))
    versions = sorted(set(entry[1] for entry in cpe_entries))
    references = []
    for reference in cve.get("references") or []:
        url = reference.get("url")
        tags = reference.get("tags") or []
        if url:
            references.append(f"{url}" + (f" [{', '.join(tags)}]" if tags else ""))
    missing = []
    if not severity:
        missing.append("Severity")
    if not products:
        missing.append("Affected Product")
    if not versions:
        missing.append("Affected Version")
    # NVD's CVE record does not expose dedicated remediation/mitigation fields.
    missing.extend(["Remediation", "Mitigation"])
    item.severity = severity
    item.cvss_score = score
    item.affected_product = "\n".join(products) if products else None
    item.affected_versions = "\n".join(versions) if versions else None
    item.nvd_description = english
    item.references_text = "\n".join(references) if references else None
    item.remediation = None
    item.mitigation = None
    item.nvd_missing_fields = json.dumps(missing, ensure_ascii=False)
    item.nvd_status = "partial" if missing else "success"
    item.nvd_error = None
    item.review_status = "under_review" if item.review_status == "new" else item.review_status
    item.updated_at = datetime.utcnow()
    db.commit()


def send_jira_ticket(item: ThreatIntelligence) -> dict:
    base_url = (settings.jira_base_url or "").rstrip("/")
    email = settings.jira_email
    token = settings.jira_api_token
    project_key = settings.jira_project_key
    issue_type = settings.jira_issue_type
    if not all((base_url, email, token, project_key)):
        raise RuntimeError("Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY.")
    summary = f"{item.cve_id} - {item.affected_product or 'Vulnerability review'}"
    description = "\n".join([
        f"CVE: {item.cve_id}",
        f"Severity: {item.severity or 'Data not found in NVD'}",
        f"CVSS: {item.cvss_score if item.cvss_score is not None else 'Data not found in NVD'}",
        f"Affected Product: {item.affected_product or 'Data not found in NVD'}",
        f"Affected Version: {item.affected_versions or 'Data not found in NVD'}",
        f"Remediation: {item.remediation or 'Data not found in NVD'}",
        f"Mitigation: {item.mitigation or 'Data not found in NVD'}",
        f"Description: {item.description or 'Not available'}",
        f"Source channel: {item.source_channel or 'Not available'}",
        f"Original message:\n{item.source_message or 'Not available'}",
        f"NVD: {item.nvd_url or f'https://nvd.nist.gov/vuln/detail/{item.cve_id}'}",
        f"References:\n{item.references_text or 'None listed in NVD'}",
    ])
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary[:250],
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description[:30000]}]}],
            },
            "labels": ["vulnerability", "threat-intelligence"],
        }
    }
    with httpx.Client(timeout=30, follow_redirects=True, auth=(email, token)) as client:
        response = client.post(f"{base_url}/rest/api/3/issue", json=payload, headers={"Accept": "application/json"})
        response.raise_for_status()
        created = response.json()
    key = created.get("key")
    if not key:
        raise httpx.HTTPStatusError("Jira response did not include an issue key.", request=response.request, response=response)
    return {"key": key, "url": f"{base_url}/browse/{quote(key)}"}


async def telegram_scheduler_loop() -> None:
    while True:
        db = SessionLocal()
        try:
            schedule = db.scalar(select(TelegramScanSchedule).order_by(TelegramScanSchedule.id))
            now = datetime.utcnow()
            if schedule and schedule.enabled:
                try:
                    hour, minute = (int(part) for part in schedule.scan_time.split(":"))
                    scheduled_time = time(hour=hour, minute=minute)
                except (ValueError, TypeError):
                    scheduled_time = time(hour=2, minute=0)
                due_today = now.time() >= scheduled_time
                same_day = schedule.last_run_date is not None and schedule.last_run_date.date() == now.date()
                day_matches = schedule.frequency == "daily" or now.weekday() == schedule.day_of_week
                feeds_exist = db.scalar(select(TelegramFeed.id).where(TelegramFeed.enabled.is_(True)).limit(1)) is not None
                if due_today and day_matches and not same_day and feeds_exist:
                    run = TelegramScanRun(
                        mode="new",
                        status="pending",
                        channels_total=db.query(TelegramFeed).filter(TelegramFeed.enabled.is_(True)).count(),
                    )
                    db.add(run)
                    schedule.last_run_date = now
                    db.commit()
                    db.refresh(run)
                    run_id = run.id
                    db.close()
                    await collect_telegram_scan(run_id)
                    await asyncio.sleep(30)
                    continue
        except Exception:
            db.rollback()
        finally:
            try:
                db.close()
            except Exception:
                pass
        await asyncio.sleep(30)
