import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models.application import Application
from app.models.equipment import Equipment
from app.models.feed import Feed
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.models.scan_schedule import ScanSchedule
from app.models.security_identifier import SecurityIdentifier
from app.models.sync_job import SyncJob
from app.services.asset_intelligence import save_identifier_from_asset
from app.services.sync_jobs import create_sync_job, update_sync_job
from app.services.vulnerability_intelligence import sync_nvd_incremental


SUPPORTED_FREQUENCIES = {
    "hourly": timedelta(hours=1),
    "every_2_hours": timedelta(hours=2),
    "every_6_hours": timedelta(hours=6),
    "daily": timedelta(days=1),
    "every_2_days": timedelta(days=2),
    "weekly": timedelta(days=7),
}


def _parse_scan_time(scan_time: str) -> tuple[int, int]:
    try:
        hour, minute = scan_time.split(":", 1)
        hour_int, minute_int = int(hour), int(minute)
    except (ValueError, AttributeError):
        raise ValueError("Scan time must use HH:MM format.")
    if not 0 <= hour_int <= 23 or not 0 <= minute_int <= 59:
        raise ValueError("Scan time must use a valid 24-hour time.")
    return hour_int, minute_int


def calculate_next_scan(
    scan_time: str,
    frequency: str = "daily",
    now: datetime | None = None,
) -> datetime:
    now = now or datetime.now()
    if frequency not in SUPPORTED_FREQUENCIES:
        raise ValueError("Unsupported scan frequency.")

    if frequency in {"hourly", "every_2_hours", "every_6_hours"}:
        interval = SUPPORTED_FREQUENCIES[frequency]
        return now.replace(second=0, microsecond=0) + interval

    hour, minute = _parse_scan_time(scan_time)
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    interval = SUPPORTED_FREQUENCIES[frequency]
    while candidate <= now:
        candidate += interval
    return candidate


def get_or_create_schedule(db):
    schedule = db.scalar(select(ScanSchedule).order_by(ScanSchedule.id).limit(1))
    if schedule is None:
        schedule = ScanSchedule(enabled=False, frequency="daily", scan_time="02:00")
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


def configure_schedule(db, *, enabled: bool, frequency: str, scan_time: str) -> ScanSchedule:
    if frequency not in SUPPORTED_FREQUENCIES:
        raise ValueError("Unsupported scan frequency.")
    _parse_scan_time(scan_time)
    schedule = get_or_create_schedule(db)
    schedule.enabled = enabled
    schedule.frequency = frequency
    schedule.scan_time = scan_time
    schedule.next_scan_at = (
        calculate_next_scan(scan_time, frequency) if enabled else None
    )
    schedule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(schedule)
    return schedule


def _set_scan_started(job_id: int, *, scheduled: bool = False) -> None:
    db = SessionLocal()
    try:
        schedule = get_or_create_schedule(db)
        schedule.last_job_id = job_id
        schedule.last_scan_at = datetime.now()
        schedule.last_status = "running"
        schedule.last_error = None
        schedule.next_scan_at = (
            calculate_next_scan(schedule.scan_time, schedule.frequency)
            if schedule.enabled else None
        )
        db.commit()
    finally:
        db.close()


def _run_scan_job(job_id: int, *, scheduled: bool = False) -> None:
    db = SessionLocal()
    job = db.get(SyncJob, job_id)
    try:
        asset_models = [
            ("equipment", Equipment),
            ("operating_system", OperatingSystem),
            ("application", Application),
            ("library", Library),
        ]
        total_assets = sum(len(db.scalars(select(model)).all()) for _, model in asset_models)

        if total_assets == 0:
            update_sync_job(db, job, status="completed", processed=0, total=0,
                current_step="No assets are defined in the asset inventory",
                result={"status":"no_assets","message":"Scan started successfully, but no assets are defined in the asset inventory.","total_assets":0,"scannable_assets":0,"discovered_candidates":0})
            return

        update_sync_job(db, job, status="running", processed=0, total=total_assets,
            current_step="Preparing asset inventory for vulnerability discovery")

        processed_assets = 0
        for asset_type, model in asset_models:
            for asset in db.scalars(select(model)).all():
                try:
                    save_identifier_from_asset(db, asset_type, asset.id)
                except Exception:
                    pass
                processed_assets += 1
                update_sync_job(db, job, processed=processed_assets, total=total_assets,
                    current_step=f"Preparing {asset_type} #{asset.id}")

        db.commit()

        scannable_assets = len(db.scalars(
            select(SecurityIdentifier).where(SecurityIdentifier.cpe.is_not(None))
        ).all())

        if scannable_assets == 0:
            update_sync_job(db, job, status="completed", processed=total_assets, total=total_assets,
                current_step="No scannable assets were found",
                result={"status":"no_scannable_assets","message":"Assets exist, but no asset has a resolved CPE for NVD vulnerability discovery.","total_assets":total_assets,"scannable_assets":0,"discovered_candidates":0})
            return

        feed = db.scalar(select(Feed).where(
            Feed.feed_type == "nvd_cve", Feed.enabled.is_(True)
        ).order_by(Feed.id))
        if feed is None:
            update_sync_job(db, job, status="failed",
                error_message="No enabled NVD CVE feed is configured.")
            return

        update_sync_job(db, job, status="running", processed=0, total=scannable_assets,
            current_step="Running vulnerability discovery against asset inventory")

        result = sync_nvd_incremental(db, feed, days_back=5, job=job)
        update_sync_job(db, job, status="completed", processed=scannable_assets,
            total=scannable_assets, current_step="Vulnerability discovery completed", result=result)
    except Exception as error:
        update_sync_job(db, job, status="failed",
            error_message=f"{error.__class__.__name__}: synchronization failed.")
    finally:
        status_db = SessionLocal()
        try:
            schedule = get_or_create_schedule(status_db)
            finished_job = status_db.get(SyncJob, job_id)
            if finished_job and finished_job.status == "completed" and finished_job.result_summary:
                import json
                try:
                    job_result = json.loads(finished_job.result_summary)
                except json.JSONDecodeError:
                    job_result = {}
                schedule.last_status = job_result.get("status") or finished_job.status
            else:
                schedule.last_status = finished_job.status if finished_job else "failed"
            schedule.last_error = finished_job.error_message if finished_job else "Scan job was not found."
            schedule.next_scan_at = (
                calculate_next_scan(schedule.scan_time, schedule.frequency)
                if schedule.enabled else None
            )
            schedule.updated_at = datetime.utcnow()
            status_db.commit()
        finally:
            status_db.close()
        db.close()


def start_scan(db, *, scheduled: bool = False) -> SyncJob:
    existing_running = db.scalar(select(SyncJob).where(
        SyncJob.job_type == "nvd",
        SyncJob.status.in_(["pending", "running"])
    ).order_by(SyncJob.id.desc()).limit(1))
    if existing_running:
        return existing_running

    total = len(db.scalars(
        select(SecurityIdentifier).where(SecurityIdentifier.cpe.is_not(None))
    ).all())
    job = create_sync_job(db, "nvd", total=total)
    _set_scan_started(job.id, scheduled=scheduled)

    loop = asyncio.get_running_loop()
    loop.create_task(asyncio.to_thread(_run_scan_job, job.id, scheduled=scheduled))
    return job


async def scheduler_loop() -> None:
    while True:
        try:
            db = SessionLocal()
            try:
                schedule = get_or_create_schedule(db)
                now = datetime.now()
                if schedule.enabled and schedule.next_scan_at is not None and now >= schedule.next_scan_at:
                    running = db.scalar(select(SyncJob).where(
                        SyncJob.job_type == "nvd",
                        SyncJob.status.in_(["pending", "running"])
                    ).order_by(SyncJob.id.desc()).limit(1))
                    if running is None:
                        start_scan(db)
                    else:
                        schedule.next_scan_at = calculate_next_scan(
                            schedule.scan_time, schedule.frequency, now
                        )
                        db.commit()
            finally:
                db.close()
        except Exception:
            pass
        await asyncio.sleep(20)
