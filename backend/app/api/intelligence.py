from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feed import Feed
from app.models.security_identifier import SecurityIdentifier
from app.models.vulnerability import Vulnerability
from app.services.cpe_resolver import resolve_cpe
from app.services.vulnerability_intelligence import (
    get_asset_vulnerabilities,
    sync_cisa_kev,
    sync_nvd_for_cpe,
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


@router.post("/assets/{asset_type}/{asset_id}/sync")
def sync_asset_vulnerabilities_api(
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

    if identifier is None or not identifier.cpe:
        raise HTTPException(
            status_code=400,
            detail="A CPE is required before vulnerability synchronization.",
        )

    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "nvd_cve",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )

    if feed is None:
        raise HTTPException(
            status_code=503,
            detail="No enabled NVD CVE feed is configured.",
        )

    try:
        return sync_nvd_for_cpe(
            db=db,
            feed=feed,
            cpe=identifier.cpe,
            asset_type=asset_type,
            asset_id=asset_id,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Vulnerability synchronization failed: {error.__class__.__name__}.",
        )


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


@router.post("/cisa-kev/sync")
def sync_cisa_kev_api(db: Session = Depends(get_db)):
    feed = db.scalar(
        select(Feed).where(
            Feed.feed_type == "cisa_kev",
            Feed.enabled.is_(True),
        ).order_by(Feed.id)
    )

    if feed is None:
        raise HTTPException(
            status_code=503,
            detail="No enabled CISA KEV feed is configured.",
        )

    try:
        return sync_cisa_kev(db, feed)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"CISA KEV synchronization failed: {error.__class__.__name__}.",
        )
