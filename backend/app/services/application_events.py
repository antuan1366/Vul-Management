import json
import logging
import traceback
from datetime import datetime
from typing import Any

from app.database import SessionLocal
from app.models.application_event import ApplicationEvent

logger = logging.getLogger("vul_management.events")


def record_event(
    level: str,
    category: str,
    component: str,
    event: str,
    message: str,
    *,
    details: dict[str, Any] | str | None = None,
    correlation_id: str | None = None,
    cve_id: str | None = None,
    scan_run_id: int | None = None,
    duration_ms: int | None = None,
) -> None:
    """Persist a diagnostic event without allowing logging failures to break app work."""
    safe_level = (level or "INFO").upper()[:20]
    safe_category = (category or "application")[:80]
    safe_component = (component or "application")[:100]
    safe_event = (event or "event")[:200]
    if isinstance(details, dict):
        details_text = json.dumps(details, ensure_ascii=False, default=str)
    else:
        details_text = details
    db = SessionLocal()
    try:
        db.add(ApplicationEvent(
            created_at=datetime.utcnow(),
            level=safe_level,
            category=safe_category,
            component=safe_component,
            event=safe_event,
            message=(message or "")[:10000],
            details=(details_text[:30000] if details_text else None),
            correlation_id=(correlation_id or None),
            cve_id=(cve_id or None),
            scan_run_id=scan_run_id,
            duration_ms=duration_ms,
        ))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not persist application event")
    finally:
        db.close()


def exception_details(error: BaseException) -> dict[str, str]:
    return {
        "exception_type": error.__class__.__name__,
        "exception": str(error)[:4000],
        "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__))[-20000:],
    }
