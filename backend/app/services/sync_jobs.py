import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.sync_job import SyncJob


def create_sync_job(db: Session, job_type: str, total: int = 0) -> SyncJob:
    job = SyncJob(job_type=job_type, status="pending", total=total)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_sync_job(
    db: Session,
    job: SyncJob,
    *,
    status: str | None = None,
    processed: int | None = None,
    total: int | None = None,
    current_step: str | None = None,
    result: dict | None = None,
    error_message: str | None = None,
) -> None:
    if status is not None:
        job.status = status
        if status == "running" and job.started_at is None:
            job.started_at = datetime.utcnow()
        if status in {"completed", "failed", "cancelled"}:
            job.finished_at = datetime.utcnow()

    if processed is not None:
        job.processed = processed
    if total is not None:
        job.total = total

    if job.total > 0:
        job.progress = min(100, int((job.processed / job.total) * 100))
    elif status == "completed":
        job.progress = 100

    if current_step is not None:
        job.current_step = current_step
    if result is not None:
        job.result_summary = json.dumps(result, ensure_ascii=False)
    if error_message is not None:
        job.error_message = error_message

    db.commit()


def serialize_sync_job(job: SyncJob) -> dict:
    result = None
    if job.result_summary:
        try:
            result = json.loads(job.result_summary)
        except json.JSONDecodeError:
            result = job.result_summary

    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "processed": job.processed,
        "total": job.total,
        "current_step": job.current_step,
        "result": result,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "created_at": job.created_at,
    }
