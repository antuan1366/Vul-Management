from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.application import Application
from app.models.equipment import Equipment
from app.models.feed import Feed
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.models.security_identifier import SecurityIdentifier
from app.models.vulnerability import Vulnerability
from app.services.cpe_resolver import resolve_cpe
from app.services.asset_intelligence import save_identifier_from_asset
from app.services.osv_intelligence import sync_osv_for_purl
from app.models.sync_job import SyncJob
from app.services.sync_jobs import create_sync_job, update_sync_job
from app.services.vulnerability_intelligence import (
    get_asset_vulnerabilities,
    sync_cisa_kev,
    sync_nvd_for_cpe,
    sync_nvd_incremental,
)


router = APIRouter(
    prefix="/api/intelligence",
    tags=["Vulnerability Intelligence"],
)


@router.get("/cpe/resolve")
def resolve_cpe_api(
    vendor: str | None = None,
    product: str | None = None,
    model: str | None = None,
    version: str | None = None,
    db: Session = Depends(get_db),
):
    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "nvd_cpe",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )

    if feed is None:
        raise HTTPException(
            status_code=503,
            detail="No enabled NVD CPE feed is configured.",
        )

    try:
        return {
            "candidates": resolve_cpe(
                url=feed.url,
                vendor=vendor,
                product=product,
                model=model,
                version=version,
                timeout=feed.timeout_seconds,
                api_key=feed.api_key,
            )
        }
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"CPE lookup failed: {error.__class__.__name__}.",
        )


def _run_asset_nvd_sync_job(job_id: int, asset_type: str, asset_id: int, days_back: int) -> None:
    db = SessionLocal()
    job = db.get(SyncJob, job_id)
    try:
        identifier = db.scalar(
            select(SecurityIdentifier).where(
                SecurityIdentifier.asset_type == asset_type,
                SecurityIdentifier.asset_id == asset_id,
            )
        )
        feed = db.scalar(
            select(Feed).where(
                Feed.feed_type == "nvd_cve",
                Feed.enabled.is_(True),
            ).order_by(Feed.id)
        )
        if identifier is None or not identifier.cpe:
            update_sync_job(db, job, status="failed", error_message="A CPE is required before vulnerability discovery.")
            return
        if feed is None:
            update_sync_job(db, job, status="failed", error_message="No enabled NVD CVE feed is configured.")
            return
        update_sync_job(db, job, status="running", processed=0, total=1, current_step=f"Discovering NVD findings for {asset_type} #{asset_id}")
        result = sync_nvd_for_cpe(db, feed, identifier.cpe, asset_type, asset_id, days_back=days_back)
        update_sync_job(db, job, status="completed", processed=1, total=1, current_step="Asset vulnerability discovery completed", result=result)
    except Exception as error:
        update_sync_job(db, job, status="failed", error_message=f"{error.__class__.__name__}: synchronization failed.")
    finally:
        db.close()


@router.post("/assets/{asset_type}/{asset_id}/sync")
def sync_asset_vulnerabilities_api(
    asset_type: str,
    asset_id: int,
    background_tasks: BackgroundTasks,
    days_back: int = Query(default=5, ge=1, le=120),
    db: Session = Depends(get_db),
):
    identifier = db.scalar(
        select(SecurityIdentifier).where(
            SecurityIdentifier.asset_type == asset_type,
            SecurityIdentifier.asset_id == asset_id,
        )
    )
    if identifier is None or not identifier.cpe:
        raise HTTPException(status_code=400, detail="A CPE is required before vulnerability synchronization.")

    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "nvd_cve",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )
    if feed is None:
        raise HTTPException(status_code=503, detail="No enabled NVD CVE feed is configured.")

    job = create_sync_job(db, "nvd_asset", total=1)
    background_tasks.add_task(_run_asset_nvd_sync_job, job.id, asset_type, asset_id, days_back)
    return {"job_id": job.id, "status": "started", "asset_type": asset_type, "asset_id": asset_id, "days_back": days_back}



@router.post("/assets/{asset_type}/{asset_id}/refresh-identifiers")
def refresh_asset_identifiers(
    asset_type: str,
    asset_id: int,
    db: Session = Depends(get_db),
):
    try:
        return save_identifier_from_asset(db, asset_type, asset_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post("/assets/{asset_type}/{asset_id}/sync-osv")
def sync_asset_osv_api(
    asset_type: str,
    asset_id: int,
    db: Session = Depends(get_db),
):
    identifier = db.scalar(
        select(SecurityIdentifier).where(
            SecurityIdentifier.asset_type == asset_type,
            SecurityIdentifier.asset_id == asset_id,
        )
    )
    if identifier is None or not identifier.purl:
        raise HTTPException(status_code=400, detail="A PURL is required before OSV synchronization.")

    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "osv",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )
    if feed is None:
        raise HTTPException(status_code=503, detail="No enabled OSV feed is configured.")

    try:
        return sync_osv_for_purl(db, feed, purl=identifier.purl, asset_type=asset_type, asset_id=asset_id)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"OSV synchronization failed: {error.__class__.__name__}.")


@router.get("/assets/{asset_type}/{asset_id}/vulnerabilities")
def get_asset_vulnerabilities_api(
    asset_type: str,
    asset_id: int,
    db: Session = Depends(get_db),
):
    return get_asset_vulnerabilities(
        db=db,
        asset_type=asset_type,
        asset_id=asset_id,
    )


@router.get("/vulnerabilities")
def list_vulnerabilities_api(
    kev_only: bool = False,
    severity: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Vulnerability)

    if kev_only:
        query = query.where(Vulnerability.cisa_kev.is_(True))

    if severity:
        query = query.where(Vulnerability.severity == severity.upper())

    items = db.scalars(
        query.order_by(
            Vulnerability.cisa_kev.desc(),
            Vulnerability.cvss_score.desc(),
            Vulnerability.cve_id,
        )
    ).all()

    return {
        "items": items,
        "total": len(items),
    }




def _run_nvd_sync_job(job_id: int, days_back: int) -> None:
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
            update_sync_job(db, job, status="failed", error_message="No enabled NVD CVE feed is configured.")
            return
        sync_nvd_incremental(db, feed, days_back=days_back, job=job)
    except Exception as error:
        update_sync_job(db, job, status="failed", error_message=f"{error.__class__.__name__}: synchronization failed.")
    finally:
        db.close()


@router.post("/nvd/sync")
def sync_nvd_api(
    background_tasks: BackgroundTasks,
    days_back: int = Query(default=7, ge=1, le=120),
    db: Session = Depends(get_db),
):
    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "nvd_cve",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )
    if feed is None:
        raise HTTPException(status_code=503, detail="No enabled NVD CVE feed is configured.")

    total = len(db.scalars(
        select(SecurityIdentifier).where(SecurityIdentifier.cpe.is_not(None))
    ).all())
    job = create_sync_job(db, "nvd", total=total)
    background_tasks.add_task(_run_nvd_sync_job, job.id, days_back)
    return {"job_id": job.id, "status": "started", "days_back": days_back, "total_assets": total}


def _run_cisa_sync_job(job_id: int) -> None:
    db = SessionLocal()
    job = db.get(SyncJob, job_id)
    try:
        feed = db.scalar(
            select(Feed).where(
                Feed.feed_type == "cisa_kev",
                Feed.enabled.is_(True),
            ).order_by(Feed.id)
        )
        if feed is None:
            update_sync_job(db, job, status="failed", error_message="No enabled CISA KEV feed is configured.")
            return
        update_sync_job(db, job, status="running", processed=0, total=1, current_step="Downloading CISA KEV catalog")
        result = sync_cisa_kev(db, feed)
        update_sync_job(db, job, status="completed", processed=1, total=1, current_step="CISA KEV enrichment completed", result=result)
    except Exception as error:
        update_sync_job(db, job, status="failed", error_message=f"{error.__class__.__name__}: synchronization failed.")
    finally:
        db.close()


@router.post("/cisa-kev/sync")
def sync_cisa_kev_api(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "cisa_kev",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )
    if feed is None:
        raise HTTPException(status_code=503, detail="No enabled CISA KEV feed is configured.")

    job = create_sync_job(db, "cisa_kev", total=1)
    background_tasks.add_task(_run_cisa_sync_job, job.id)
    return {"job_id": job.id, "status": "started"}


def _run_cpe_extraction_job(job_id: int) -> None:
    db = SessionLocal()
    job = db.get(SyncJob, job_id)
    models = [
        ("equipment", Equipment),
        ("operating_system", OperatingSystem),
        ("application", Application),
        ("library", Library),
    ]
    processed = 0
    resolved = 0
    try:
        total = sum(len(db.scalars(select(model)).all()) for _, model in models)
        update_sync_job(db, job, status="running", total=total, processed=0, current_step="Extracting asset identifiers")
        for asset_type, model in models:
            assets = db.scalars(select(model)).all()
            for asset in assets:
                try:
                    result = save_identifier_from_asset(db, asset_type, asset.id)
                    if result.get("resolved_cpe") or result.get("purl"):
                        resolved += 1
                except Exception:
                    pass
                processed += 1
                update_sync_job(
                    db, job, processed=processed, total=total,
                    current_step=f"Processed {asset_type} #{asset.id}",
                )
        result = {"processed_assets": processed, "resolved_identifiers": resolved}
        update_sync_job(db, job, status="completed", processed=processed, total=total, current_step="Identifier extraction completed", result=result)
    except Exception as error:
        update_sync_job(db, job, status="failed", error_message=f"{error.__class__.__name__}: identifier extraction failed.")
    finally:
        db.close()


@router.post("/assets/refresh-identifiers")
def refresh_all_asset_identifiers(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    total = sum(
        len(db.scalars(select(model)).all())
        for model in (Equipment, OperatingSystem, Application, Library)
    )
    job = create_sync_job(db, "cpe_extraction", total=total)
    background_tasks.add_task(_run_cpe_extraction_job, job.id)
    return {"job_id": job.id, "status": "started", "total_assets": total}
