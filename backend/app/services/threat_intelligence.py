import asyncio
import json
import os
import re
import threading
from datetime import datetime, time
from pathlib import Path
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.services.application_events import record_event, exception_details
import time as monotonic_time
from app.core.config import settings
from app.models.feed import Feed
from app.models.threat_intelligence import TelegramFeed, TelegramScanResult, TelegramScanRun, TelegramScanSchedule, ThreatIntelligence

CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)

# NVD's unauthenticated API limit is 5 requests per 30 seconds. Keep a
# process-wide limiter so scan workers and manual enrichment share the same pace.
_NVD_REQUEST_LOCK = threading.Lock()
_NVD_NEXT_REQUEST_AT = 0.0
_NVD_MIN_REQUEST_INTERVAL_SECONDS = 8.0


def _wait_for_nvd_request_slot() -> None:
    global _NVD_NEXT_REQUEST_AT
    with _NVD_REQUEST_LOCK:
        now = monotonic_time.monotonic()
        if _NVD_NEXT_REQUEST_AT > now:
            import time as time_module
            time_module.sleep(_NVD_NEXT_REQUEST_AT - now)
        _NVD_NEXT_REQUEST_AT = monotonic_time.monotonic() + _NVD_MIN_REQUEST_INTERVAL_SECONDS


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
    record_event("INFO", "telegram", "Telegram scanner", "scan_started",
                 f"Telegram scan run {run_id} started in mode {run.mode}.",
                 scan_run_id=run_id, details={"mode": run.mode, "start_date": str(run.start_date)})
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
                record_event("ERROR", "telegram", "Telegram scanner", "feed_scan_failed",
                             f"Failed to scan Telegram channel @{feed.channel_username}: {error.__class__.__name__}: {str(error)[:500]}",
                             scan_run_id=run_id, details=exception_details(error))
        run.finished_at = datetime.utcnow()
        result_count = db.query(TelegramScanResult).filter(TelegramScanResult.scan_run_id == run.id).count()
        if result_count:
            run.status = "nvd_scanning"
        else:
            run.status = "completed_with_errors" if run.error_message else "completed"
        db.commit()
        completed_run_id = run.id
        record_event("WARNING" if run.error_message else "INFO", "telegram", "Telegram scanner", "scan_collection_finished",
                     f"Telegram collection phase finished with status {run.status}.",
                     scan_run_id=run_id, details={"channels_total": run.channels_total,
                     "channels_processed": run.channels_processed, "messages_processed": run.messages_processed,
                     "cve_occurrences": run.cve_occurrences, "error_message": run.error_message})
        try:
            await client.disconnect()
        except Exception:
            pass
        if result_count:
            # NVD enrichment is a separate background phase; the scan response and UI remain usable.
            # Run NVD enrichment in the same managed task so it cannot become an untracked fire-and-forget task.
            await enrich_scan_run_from_nvd(completed_run_id)
    except Exception as error:
        run.status = "failed"
        run.error_message = f"{error.__class__.__name__}: {str(error)[:500]}"
        run.finished_at = datetime.utcnow()
        db.commit()
        record_event("ERROR", "telegram", "Telegram scanner", "scan_failed",
                     f"Telegram scan run {run_id} failed: {error.__class__.__name__}: {str(error)[:500]}",
                     scan_run_id=run_id, details=exception_details(error))
    finally:
        db.close()


async def enrich_scan_run_from_nvd(run_id: int) -> None:
    """Enrich unique CVEs in the background, saving each result as soon as its lookup finishes."""
    db = SessionLocal()
    try:
        run = db.get(TelegramScanRun, run_id)
        if run is None:
            return
        run.status = "nvd_scanning"
        rows = db.scalars(
            select(TelegramScanResult)
            .where(TelegramScanResult.scan_run_id == run_id)
            .order_by(TelegramScanResult.cve_id.asc(), TelegramScanResult.id.asc())
        ).all()
        by_cve: dict[str, list[TelegramScanResult]] = {}
        for item in rows:
            by_cve.setdefault(item.cve_id, []).append(item)

        work_cves = []
        # Retry not-found CVEs on later scans because sources may publish or correct
        # records after an earlier lookup. Successful/partial results remain cached.
        terminal_success = {"success", "partial"}
        for cve_id, items in by_cve.items():
            existing = next((item for item in items if item.nvd_status in terminal_success), None)
            if existing is not None:
                for item in items:
                    if item.id != existing.id and item.nvd_status not in terminal_success:
                        _copy_nvd_fields(existing, item)
                continue
            for item in items:
                item.nvd_status = "queued"
                item.nvd_error = None
            work_cves.append(cve_id)
        db.commit()
        db.close()

        # Work in the same CVE order as the Scan Result table. The shared HTTP
        # limiter controls request spacing, including retries and manual lookups.
        for cve_id in sorted(work_cves):
            await asyncio.to_thread(_enrich_cve_for_scan_run, run_id, cve_id)

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
            record_event("WARNING" if run.status == "completed_with_errors" else "INFO",
                         "nvd", "NVD enrichment", "scan_enrichment_finished",
                         f"NVD enrichment phase finished with status {run.status}.",
                         scan_run_id=run_id,
                         details={"failed_lookups": failures, "finished_at": str(run.finished_at)})
    except Exception as error:
        db = SessionLocal()
        try:
            run = db.get(TelegramScanRun, run_id)
            if run:
                run.status = "completed_with_errors"
                detail = f"NVD enrichment worker: {error.__class__.__name__}: {str(error)[:250]}"
                run.error_message = (run.error_message + "\n" if run.error_message else "") + detail
                run.finished_at = datetime.utcnow()
                db.commit()
                record_event("ERROR", "nvd", "NVD enrichment", "worker_failed",
                             detail, scan_run_id=run_id, details=exception_details(error))
        finally:
            db.close()
    finally:
        try:
            db.close()
        except Exception:
            pass


def _copy_nvd_fields(source: TelegramScanResult, target: TelegramScanResult) -> None:
    for field in (
        "severity", "cvss_score", "affected_product", "affected_versions",
        "remediation", "mitigation", "nvd_description", "references_text",
        "nvd_missing_fields", "nvd_status", "nvd_error",
    ):
        setattr(target, field, getattr(source, field))
    target.updated_at = datetime.utcnow()


def _enrich_cve_for_scan_run(run_id: int, cve_id: str) -> None:
    """Look up a CVE once and copy the returned NVD fields to all matching scan rows."""
    db = SessionLocal()
    try:
        items = db.scalars(
            select(TelegramScanResult)
            .where(
                TelegramScanResult.scan_run_id == run_id,
                TelegramScanResult.cve_id == cve_id,
            )
            .order_by(TelegramScanResult.id.asc())
        ).all()
        if not items:
            return
        representative = items[0]
        started = monotonic_time.perf_counter()
        record_event(
            "INFO", "nvd", "NVD enrichment", "lookup_started",
            f"Started multi-source CVE lookup for {cve_id}.",
            cve_id=cve_id, scan_run_id=run_id,
            details={"matching_scan_results": len(items)},
        )
        try:
            enrich_scan_result_from_sources(db, representative)
            elapsed_ms = int((monotonic_time.perf_counter() - started) * 1000)
            record_event(
                "INFO" if representative.nvd_status in {"success", "partial"} else "WARNING",
                "nvd", "NVD enrichment", "lookup_finished",
                f"Multi-source CVE lookup finished with status {representative.nvd_status}.",
                cve_id=cve_id, scan_run_id=run_id, duration_ms=elapsed_ms,
                details={"nvd_status": representative.nvd_status,
                         "missing_fields": representative.nvd_missing_fields},
            )
        except LookupError as error:
            # The not-found result has already been saved on the representative.
            record_event(
                "WARNING", "nvd", "NVD enrichment", "cve_not_found",
                str(error), cve_id=cve_id, scan_run_id=run_id,
                duration_ms=int((monotonic_time.perf_counter() - started) * 1000),
            )
        except (httpx.HTTPError, ValueError) as error:
            representative.nvd_status = "error"
            representative.nvd_error = f"NVD request failed: {error.__class__.__name__}: {str(error)[:500]}"
            db.commit()
            record_event(
                "ERROR", "nvd", "NVD enrichment", "lookup_failed",
                f"NVD lookup failed for {cve_id}: {error.__class__.__name__}: {str(error)[:500]}",
                cve_id=cve_id, scan_run_id=run_id,
                duration_ms=int((monotonic_time.perf_counter() - started) * 1000),
                details=exception_details(error),
            )
        except Exception as error:
            record_event(
                "ERROR", "nvd", "NVD enrichment", "unexpected_lookup_error",
                f"Unexpected error while looking up {cve_id}: {error.__class__.__name__}: {str(error)[:500]}",
                cve_id=cve_id, scan_run_id=run_id,
                duration_ms=int((monotonic_time.perf_counter() - started) * 1000),
                details=exception_details(error),
            )
            raise
        for item in items[1:]:
            _copy_nvd_fields(representative, item)
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
    headers = {"Accept": "application/json", "User-Agent": "Vul-Management/3.2.0"}
    if feed and feed.api_key:
        headers["apiKey"] = feed.api_key
    timeout = feed.timeout_seconds if feed else 20
    request_url = feed.url if feed else "https://services.nvd.nist.gov/rest/json/cves/2.0"
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = None
        max_attempts = 8
        for attempt in range(max_attempts):
            attempt_started = monotonic_time.perf_counter()
            _wait_for_nvd_request_slot()
            try:
                response = client.get(request_url, params={"cveId": item.cve_id})
                request_ms = int((monotonic_time.perf_counter() - attempt_started) * 1000)
                record_event(
                    "WARNING" if response.status_code in {429, 503} else "INFO",
                    "nvd", "NVD HTTP client", "http_response",
                    f"NVD returned HTTP {response.status_code} for {item.cve_id} (attempt {attempt + 1}/{max_attempts}).",
                    cve_id=item.cve_id, duration_ms=request_ms,
                    details={"http_status": response.status_code, "attempt": attempt + 1,
                             "timeout_seconds": timeout, "endpoint": request_url,
                             "retry_after": response.headers.get("Retry-After")},
                )
            except httpx.HTTPError as error:
                request_ms = int((monotonic_time.perf_counter() - attempt_started) * 1000)
                record_event(
                    "WARNING" if attempt < max_attempts - 1 else "ERROR",
                    "nvd", "NVD HTTP client", "http_request_exception",
                    f"NVD request exception for {item.cve_id}: {error.__class__.__name__}: {str(error)[:500]}",
                    cve_id=item.cve_id, duration_ms=request_ms,
                    details={**exception_details(error), "attempt": attempt + 1,
                             "timeout_seconds": timeout, "endpoint": request_url},
                )
                if attempt >= max_attempts - 1:
                    raise
                import time as time_module
                time_module.sleep(min(300, 10 * (2 ** attempt)))
                continue
            if response.status_code not in {429, 503}:
                break
            if attempt >= max_attempts - 1:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            try:
                wait_seconds = max(30, min(900, int(retry_after))) if retry_after else min(900, 60 * (2 ** attempt))
            except ValueError:
                wait_seconds = min(900, 60 * (2 ** attempt))
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
    if not english:
        missing.append("Description")
    # NVD's CVE record does not expose dedicated remediation/mitigation fields.
    item.severity = severity
    item.cvss_score = score
    item.affected_product = "\n".join(products) if products else None
    item.affected_versions = "\n".join(versions) if versions else None
    item.nvd_description = english
    item.references_text = "\n".join(references) if references else None
    # Remediation and mitigation are administrator-managed in Vulnerabilities;
    # NVD lookup must not treat them as required NVD fields.
    item.nvd_missing_fields = json.dumps(missing, ensure_ascii=False)
    item.nvd_status = "partial" if missing else "success"
    item.nvd_error = None
    item.updated_at = datetime.utcnow()
    db.commit()


_GHSA_REQUEST_LOCK = threading.Lock()
_GHSA_NEXT_REQUEST_AT = 0.0


def _wait_for_github_request_slot(authenticated: bool) -> None:
    """Respect GitHub's public API quota when the feed has no token."""
    global _GHSA_NEXT_REQUEST_AT
    minimum_interval = 1.0 if authenticated else 65.0
    with _GHSA_REQUEST_LOCK:
        now = monotonic_time.monotonic()
        if _GHSA_NEXT_REQUEST_AT > now:
            import time as time_module
            time_module.sleep(_GHSA_NEXT_REQUEST_AT - now)
        _GHSA_NEXT_REQUEST_AT = monotonic_time.monotonic() + minimum_interval


def _source_headers(feed: Feed, github: bool = False) -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "Vul-Management/3.2.0"}
    if github:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if feed.api_key:
            headers["Authorization"] = f"Bearer {feed.api_key}"
    elif feed.auth_type == "api_key" and feed.api_key:
        headers["apiKey"] = feed.api_key
    elif feed.auth_type == "bearer" and feed.api_key:
        headers["Authorization"] = f"Bearer {feed.api_key}"
    return headers


def _source_get_json(
    feed: Feed,
    url: str,
    cve_id: str,
    params: dict | None = None,
    github: bool = False,
):
    """GET JSON with conservative retries for transient errors and source-specific pacing."""
    with httpx.Client(
        timeout=max(10, feed.timeout_seconds),
        follow_redirects=True,
        headers=_source_headers(feed, github=github),
    ) as client:
        for attempt in range(4):
            if github:
                _wait_for_github_request_slot(authenticated=bool(feed.api_key))
            try:
                response = client.get(url, params=params)
            except httpx.HTTPError:
                if attempt >= 3:
                    raise
                import time as time_module
                time_module.sleep(min(120, 10 * (2 ** attempt)))
                continue

            if response.status_code == 404:
                return None
            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                raise httpx.HTTPStatusError(
                    f"{feed.name} rate limit exhausted.",
                    request=response.request,
                    response=response,
                )
            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt >= 3:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    wait_seconds = max(1, min(900, int(retry_after))) if retry_after else min(300, 15 * (2 ** attempt))
                except ValueError:
                    wait_seconds = min(300, 15 * (2 ** attempt))
                response.close()
                import time as time_module
                time_module.sleep(wait_seconds)
                continue
            response.raise_for_status()
            return response.json()
    return None


def _cve_program_record_url(feed: Feed, cve_id: str) -> str:
    parts = cve_id.upper().split("-")
    if len(parts) != 3 or not parts[2].isdigit() or len(parts[2]) < 4:
        raise ValueError(f"Invalid CVE identifier: {cve_id}")
    year, sequence = parts[1], parts[2]
    bucket = f"{sequence[:-3]}xxx"
    return f"{feed.url.rstrip('/')}/{year}/{bucket}/{cve_id.upper()}.json"


def _severity_from_score(score):
    if score is None:
        return None
    try:
        score = float(score)
    except (TypeError, ValueError):
        return None
    return "CRITICAL" if score >= 9 else "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"


def _extract_cve_program_record(payload: dict, record_url: str) -> dict | None:
    metadata = payload.get("cveMetadata") or {}
    if str(metadata.get("state") or "").upper() in {"REJECTED", "REJECT"}:
        return None

    containers = payload.get("containers") or {}
    cna = containers.get("cna") or {}
    adp = containers.get("adp") or []
    containers_to_check = [cna] + [item for item in adp if isinstance(item, dict)]

    descriptions = cna.get("descriptions") or []
    description = next(
        (entry.get("value") for entry in descriptions
         if entry.get("lang") == "en" and entry.get("value")),
        None,
    )

    score = None
    severity = None
    for container in containers_to_check:
        for metric in container.get("metrics") or []:
            if not isinstance(metric, dict):
                continue
            for key in ("cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0", "cvssV2"):
                cvss = metric.get(key)
                if not isinstance(cvss, dict):
                    continue
                score = cvss.get("baseScore")
                severity = cvss.get("baseSeverity") or cvss.get("severity")
                if not severity:
                    severity = _severity_from_score(score)
                break
            if score is not None or severity:
                break
        if score is not None or severity:
            break

    products = set()
    versions = set()
    for container in containers_to_check:
        for affected in container.get("affected") or []:
            if not isinstance(affected, dict):
                continue
            product = str(affected.get("product") or "").strip()
            vendor = str(affected.get("vendor") or "").strip()
            bad_values = {"", "n/a", "unknown", "unspecified", "*"}
            product_valid = product.lower() not in bad_values
            vendor_valid = vendor.lower() not in bad_values
            if product_valid:
                label = f"{vendor} {product}".strip() if vendor_valid and vendor.lower() not in product.lower() else product
                products.add(label)

            for version in affected.get("versions") or []:
                if not isinstance(version, dict):
                    continue
                if str(version.get("status") or "").lower() in {"unaffected", "unaffected by default"}:
                    continue
                current = str(version.get("version") or "").strip()
                lower = str(version.get("lessThanOrEqual") or version.get("lessThan") or "").strip()
                current_valid = current.lower() not in bad_values
                lower_valid = lower.lower() not in bad_values
                if current_valid and lower_valid:
                    operator = "<=" if version.get("lessThanOrEqual") else "<"
                    versions.add(f">= {current}, {operator} {lower}")
                elif current_valid:
                    versions.add(current)
                elif lower_valid:
                    operator = "<=" if version.get("lessThanOrEqual") else "<"
                    versions.add(f"< {lower}" if operator == "<" else f"<= {lower}")

    references = []
    for container in containers_to_check:
        for reference in container.get("references") or []:
            url = reference.get("url") if isinstance(reference, dict) else None
            if url:
                references.append(url)

    return {
        "source": "CVE Program",
        "source_url": record_url,
        "severity": severity.upper() if severity else None,
        "cvss_score": score,
        "affected_product": "\n".join(sorted(products)) or None,
        "affected_versions": "\n".join(sorted(versions)) or None,
        "description": description,
        "references": references,
    }


def _extract_github_advisory_records(payload, cve_id: str) -> dict | None:
    advisories = payload if isinstance(payload, list) else ([payload] if isinstance(payload, dict) else [])
    selected = None
    for advisory in advisories:
        if not isinstance(advisory, dict) or advisory.get("withdrawn_at"):
            continue
        identifiers = advisory.get("identifiers") or []
        has_cve = str(advisory.get("cve_id") or "").upper() == cve_id.upper()
        has_cve = has_cve or any(
            isinstance(identifier, dict)
            and str(identifier.get("type") or "").upper() == "CVE"
            and str(identifier.get("value") or "").upper() == cve_id.upper()
            for identifier in identifiers
        )
        if has_cve:
            selected = advisory
            break
    if selected is None:
        return None

    cvss_severities = selected.get("cvss_severities") or {}
    metric = cvss_severities.get("cvss_v4") or cvss_severities.get("cvss_v3") or {}
    legacy_cvss = selected.get("cvss") or {}
    score = metric.get("score")
    if score is None:
        score = legacy_cvss.get("score")
    severity = selected.get("severity") or metric.get("severity")
    if severity:
        severity = str(severity).upper()
        if severity == "MODERATE":
            severity = "MEDIUM"
    if not severity:
        severity = _severity_from_score(score)

    products = set()
    versions = set()
    references = []
    for vulnerability in selected.get("vulnerabilities") or []:
        if not isinstance(vulnerability, dict):
            continue
        package = vulnerability.get("package") or {}
        package_name = str(package.get("name") or "").strip()
        ecosystem = str(package.get("ecosystem") or "").strip()
        if package_name:
            products.add(f"{ecosystem}: {package_name}" if ecosystem else package_name)
        range_text = str(vulnerability.get("vulnerable_version_range") or "").strip()
        first_patched = vulnerability.get("first_patched_version") or {}
        first_patched_value = str(first_patched.get("identifier") or "").strip() if isinstance(first_patched, dict) else ""
        if range_text and first_patched_value:
            versions.add(f"{range_text}; first patched: {first_patched_value}")
        elif range_text:
            versions.add(range_text)
        elif first_patched_value:
            versions.add(f"first patched: {first_patched_value}")

    html_url = selected.get("html_url") or selected.get("url") or ""
    if html_url:
        references.append(html_url)
    for reference in selected.get("references") or []:
        if isinstance(reference, str):
            references.append(reference)
        elif isinstance(reference, dict) and reference.get("url"):
            references.append(reference["url"])

    return {
        "source": "GitHub Security Advisories",
        "source_url": html_url,
        "severity": severity,
        "cvss_score": score,
        "affected_product": "\n".join(sorted(products)) or None,
        "affected_versions": "\n".join(sorted(versions)) or None,
        "description": selected.get("description") or selected.get("summary"),
        "references": references,
    }


def _missing_core_fields(item: TelegramScanResult) -> list[str]:
    missing = []
    if not item.severity:
        missing.append("Severity")
    if not item.affected_product:
        missing.append("Affected Product")
    if not item.affected_versions:
        missing.append("Affected Version")
    if not item.nvd_description:
        missing.append("Description")
    return missing


def _append_source_references(item: TelegramScanResult, source: dict) -> None:
    lines = [line.strip() for line in (item.references_text or "").splitlines() if line.strip()]
    source_url = source.get("source_url")
    if source_url:
        lines.append(f"[Source: {source['source']}] {source_url}")
    lines.extend(
        f"[{source['source']}] {url}"
        for url in source.get("references") or []
        if url
    )
    item.references_text = "\n".join(dict.fromkeys(lines)) or None


def _merge_supplemental_record(item: TelegramScanResult, source: dict) -> None:
    if not item.severity and source.get("severity"):
        item.severity = source["severity"]
    if item.cvss_score is None and source.get("cvss_score") is not None:
        try:
            item.cvss_score = float(source["cvss_score"])
        except (TypeError, ValueError):
            pass
    if not item.severity and item.cvss_score is not None:
        item.severity = _severity_from_score(item.cvss_score)
    if not item.affected_product and source.get("affected_product"):
        item.affected_product = source["affected_product"]
    if not item.affected_versions and source.get("affected_versions"):
        item.affected_versions = source["affected_versions"]
    if not item.nvd_description and source.get("description"):
        item.nvd_description = source["description"]
    _append_source_references(item, source)


def enrich_scan_result_from_sources(db, item: TelegramScanResult) -> None:
    """Use NVD first, then enabled supplemental feeds to fill missing CVE fields."""
    errors = []
    sources_used = []

    try:
        enrich_scan_result_from_nvd(db, item)
        if item.nvd_status in {"success", "partial"}:
            sources_used.append("NVD")
    except LookupError as error:
        # A missing NVD record is not a transport failure; supplemental sources
        # should still be queried and a final miss should remain "not_found".
        record_event(
            "WARNING", "enrichment", "NVD", "record_not_found",
            f"NVD returned no record for {item.cve_id}: {str(error)[:200]}",
            cve_id=item.cve_id,
        )
    except (httpx.HTTPError, ValueError) as error:
        item.nvd_status = "error"
        item.nvd_error = f"NVD request failed: {error.__class__.__name__}: {str(error)[:250]}"
        errors.append(item.nvd_error)
        db.commit()

    if _missing_core_fields(item):
        feeds = db.scalars(
            select(Feed)
            .where(
                Feed.enabled.is_(True),
                Feed.feed_type.in_(["cve_program", "github_advisory"]),
            )
            .order_by(Feed.id.asc())
        ).all()
        for feed in feeds:
            if not _missing_core_fields(item):
                break
            try:
                if feed.feed_type == "cve_program":
                    record_url = _cve_program_record_url(feed, item.cve_id)
                    payload = _source_get_json(feed, record_url, item.cve_id)
                    source_data = _extract_cve_program_record(payload, record_url) if payload else None
                elif feed.feed_type == "github_advisory":
                    payload = _source_get_json(
                        feed,
                        feed.url,
                        item.cve_id,
                        params={"cve_id": item.cve_id, "per_page": 100},
                        github=True,
                    )
                    source_data = _extract_github_advisory_records(payload, item.cve_id) if payload else None
                else:
                    continue

                if source_data:
                    _merge_supplemental_record(item, source_data)
                    sources_used.append(source_data["source"])
                    db.commit()
                    record_event(
                        "INFO", "enrichment", "CVE source", "supplemental_source_found",
                        f"{source_data['source']} returned data for {item.cve_id}.",
                        cve_id=item.cve_id,
                        details={"source": source_data["source"], "missing_fields": _missing_core_fields(item)},
                    )
                else:
                    record_event(
                        "INFO", "enrichment", "CVE source", "supplemental_source_empty",
                        f"{feed.name} returned no matching record for {item.cve_id}.",
                        cve_id=item.cve_id,
                        details={"feed_id": feed.id, "feed_type": feed.feed_type},
                    )
            except (httpx.HTTPError, ValueError, TypeError, KeyError) as error:
                detail = f"{feed.name}: {error.__class__.__name__}: {str(error)[:200]}"
                errors.append(detail)
                record_event(
                    "WARNING", "enrichment", "CVE source", "supplemental_source_failed",
                    f"Supplemental lookup failed for {item.cve_id}: {detail}",
                    cve_id=item.cve_id,
                    details={"feed_id": feed.id, "feed_type": feed.feed_type, **exception_details(error)},
                )

    missing = _missing_core_fields(item)
    item.nvd_missing_fields = json.dumps(missing, ensure_ascii=False)
    item.updated_at = datetime.utcnow()
    if sources_used:
        item.nvd_status = "success" if not missing else "partial"
        item.nvd_error = None
    elif errors:
        item.nvd_status = "error"
        item.nvd_error = "All enabled CVE sources failed to return usable data. " + " | ".join(errors)[:700]
    else:
        item.nvd_status = "not_found"
        item.nvd_error = None
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
        f"Severity: {item.severity or 'Not available from enabled sources'}",
        f"CVSS: {item.cvss_score if item.cvss_score is not None else 'Not available from enabled sources'}",
        f"Affected Product: {item.affected_product or 'Not available from enabled sources'}",
        f"Affected Version: {item.affected_versions or 'Not available from enabled sources'}",
        f"Remediation: {item.remediation or 'Not available from enabled sources'}",
        f"Mitigation: {item.mitigation or 'Not available from enabled sources'}",
        f"Description: {item.description or 'Not available'}",
        f"Source channel: {item.source_channel or 'Not available'}",
        f"Original message:\n{item.source_message or 'Not available'}",
        f"NVD: {item.nvd_url or f'https://nvd.nist.gov/vuln/detail/{item.cve_id}'}",
        f"References:\n{item.references_text or 'No references returned by enabled sources'}",
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
