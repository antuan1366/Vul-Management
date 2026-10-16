from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application_event import ApplicationEvent

router = APIRouter(prefix="/api/events", tags=["Logs & Events"])


def serialize_event(item: ApplicationEvent) -> dict:
    return {
        "id": item.id,
        "created_at": item.created_at,
        "level": item.level,
        "category": item.category,
        "component": item.component,
        "event": item.event,
        "message": item.message,
        "details": item.details,
        "correlation_id": item.correlation_id,
        "cve_id": item.cve_id,
        "scan_run_id": item.scan_run_id,
        "duration_ms": item.duration_ms,
    }


@router.get("")
def list_events(
    q: str | None = None,
    level: str = "all",
    category: str = "all",
    since: datetime | None = None,
    until: datetime | None = None,
    scan_run_id: int | None = None,
    cve_id: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(ApplicationEvent)
    if level.lower() != "all":
        query = query.where(ApplicationEvent.level == level.upper())
    if category.lower() != "all":
        query = query.where(ApplicationEvent.category == category)
    if since:
        query = query.where(ApplicationEvent.created_at >= since)
    if until:
        query = query.where(ApplicationEvent.created_at <= until)
    if scan_run_id is not None:
        query = query.where(ApplicationEvent.scan_run_id == scan_run_id)
    if cve_id:
        query = query.where(ApplicationEvent.cve_id.ilike(f"%{cve_id.strip()}%"))
    if q:
        needle = f"%{q.strip()}%"
        query = query.where(or_(
            ApplicationEvent.message.ilike(needle),
            ApplicationEvent.event.ilike(needle),
            ApplicationEvent.component.ilike(needle),
            ApplicationEvent.details.ilike(needle),
            ApplicationEvent.cve_id.ilike(needle),
            ApplicationEvent.correlation_id.ilike(needle),
        ))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(ApplicationEvent.created_at.desc(), ApplicationEvent.id.desc())
        .offset(offset).limit(limit)
    ).all()
    return {"items": [serialize_event(item) for item in items], "total": total, "limit": limit, "offset": offset}
