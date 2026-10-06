import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sync_job import SyncJob
from app.services.sync_jobs import serialize_sync_job

router = APIRouter(prefix="/api/sync-jobs", tags=["Synchronization"])


@router.get("")
def list_sync_jobs(
    job_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    query = select(SyncJob).order_by(SyncJob.created_at.desc()).limit(limit)
    if job_type:
        query = select(SyncJob).where(SyncJob.job_type == job_type).order_by(SyncJob.created_at.desc()).limit(limit)
    jobs = db.scalars(query).all()
    return {"items": [serialize_sync_job(job) for job in jobs]}


@router.get("/{job_id}")
def get_sync_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(SyncJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Sync job not found.")
    return serialize_sync_job(job)
