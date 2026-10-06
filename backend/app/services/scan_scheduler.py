import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models.feed import Feed
from app.models.scan_schedule import ScanSchedule
from app.models.security_identifier import SecurityIdentifier
from app.models.sync_job import SyncJob
from app.services.sync_jobs import create_sync_job, update_sync_job
from app.services.vulnerability_intelligence import sync_nvd_incremental


def _parse_scan_time(scan_time: str) -> tuple[int, int]:
    try:
        hour, minute = scan_time.split(":", 1)
        hour_int = int(hour)
        minute_int = int(minute)
    except (ValueError, AttributeError):
        raise ValueError("Scan time must use HH:MM format.")

    if not 0 <= hour_int <= 23 or not 0 <= minute_int <= 59:
        raise ValueError("Scan time must use a valid 24-hour time.")

    return hour_int, minute_int


def calculate_next_scan(scan_time: str, now: datetime | None = None) -> datetime:
    now = now or datetime.now()
    hour, minute = _parse_scan_time(scan_time)
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def get_or_create_schedule(db):
    schedule = db.scalar(select(ScanSchedule).order_by(ScanSchedule.id).limit(1))
    if schedule is None:
        schedule = ScanSchedule(
            enabled=False,
            frequency="daily",
            scan_time="02:00",
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
    return schedule


def serialize_schedule(schedule: ScanSchedule) -> dict:
    return {
        "id": schedule.id,
        "enabled": schedule.enabled,
        "frequency": schedule.frequency,
        "scan_time": schedule.scan_time,
        "last_job_id": schedule.last_job_id,
        "last_scan_at": schedule.last_scan_at,
        "next_scan_at": schedule.next_scan_at,
        "last_status": schedule.last_status,
        "last_error": schedule.last_error,
        "updated_at": schedule.updated_at,
    }


def configure_schedule(db, *, enabled: bool, scan_time: str) -> ScanSchedule:
    _parse_scan_time(scan_time)
    schedule = get_or_create_schedule(db)
    schedule.enabled = enabled
    schedule.frequency = "daily"
    schedule.scan_time = scan_time
    schedule.next_scan_at = calculate_next_scan(scan_time) if enabled else None
    schedule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(schedule)
    return schedule


def _set_scan_started(job_id: int) -> None:
    db = SessionLocal()
    try:
        schedule = get_or_create_schedule(db)
        schedule.last_job_id = job_id
        schedule.last_scan_at = datetime.now()
        schedule.last_status = "running"
        schedule.last_error = None
        schedule.next_scan_at = (
            calculate_next_scan(schedule.scan_time)
            if schedule.enabled
            else None
        )
        db.commit()
    finally:
        db.close()


def _run_scan_job(job_id: int) -> None:
    db = SessionLocal()
    job = db.get(SyncJob, job_id)
    try:
        feed = db.scalar(
            select(Feed).where(
                Feed.feed_type == "nvd_cve",
                Feed.enabled.is_(True),
            ).order_by(Feed.id)
        )
        if feed is None:
            update_sync_job(
                db,
                job,
                status="failed",
                error_message="No enabled NVD CVE feed is configured.",
            )
            return

        total = len(
            db.scalars(
                select(SecurityIdentifier).where(
                    SecurityIdentifier.cpe.is_not(None)
                )
            ).all()
        )
        update_sync_job(
            db,
            job,
            status="running",
            processed=0,
            total=total,
            current_step="Running scheduled vulnerability discovery",
        )

        result = sync_nvd_incremental(
            db,
            feed,
            days_back=5,
            job=job,
        )

        update_sync_job(
            db,
            job,
            status="completed",
            processed=total,
            total=total,
            current_step="Vulnerability discovery completed",
            result=result,
        )
    except Exception as error:
        update_sync_job(
            db,
            job,
            status="failed",
            error_message=f"{error.__class__.__name__}: synchronization failed.",
        )
    finally:
        status_db = SessionLocal()
        try:
            schedule = get_or_create_schedule(status_db)
            finished_job = status_db.get(SyncJob, job_id)
            schedule.last_status = finished_job.status if finished_job else "failed"
            schedule.last_error = (
                finished_job.error_message if finished_job else "Scan job was not found."
            )
            schedule.next_scan_at = (
                calculate_next_scan(schedule.scan_time)
                if schedule.enabled
                else None
            )
            schedule.updated_at = datetime.utcnow()
            status_db.commit()
        finally:
            status_db.close()
        db.close()


def start_scan(db) -> SyncJob:
    schedule = get_or_create_schedule(db)

    existing_running = db.scalar(
        select(SyncJob).where(
            SyncJob.job_type == "nvd",
            SyncJob.status.in_([ "pending", "running" ]),
        ).order_by(SyncJob.id.desc()).limit(1)
    )
    if existing_running:
        return existing_running

    total = len(
        db.scalars(
            select(SecurityIdentifier).where(
                SecurityIdentifier.cpe.is_not(None)
            )
        ).all()
    )
    job = create_sync_job(db, "nvd", total=total)
    _set_scan_started(job.id)

    loop = asyncio.get_running_loop()
    loop.create_task(asyncio.to_thread(_run_scan_job, job.id))
    return job


async def scheduler_loop() -> None:
    while True:
        try:
            db = SessionLocal()
            try:
                schedule = get_or_create_schedule(db)
                now = datetime.now()

                if (
                    schedule.enabled
                    and schedule.next_scan_at is not None
                    and now >= schedule.next_scan_at
                ):
                    running = db.scalar(
                        select(SyncJob).where(
                            SyncJob.job_type == "nvd",
                            SyncJob.status.in_([ "pending", "running" ]),
                        ).order_by(SyncJob.id.desc()).limit(1)
                    )
                    if running is None:
                        start_scan(db)
                    else:
                        schedule.next_scan_at = calculate_next_scan(schedule.scan_time)
                        db.commit()
            finally:
                db.close()
        except Exception:
            pass

        await asyncio.sleep(20)
