from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.equipment import Equipment
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.models.feed import Feed
from app.services.cpe_resolver import resolve_cpe
from app.services.security_identifiers import upsert_identifier
from app.schemas.security_identifier import SecurityIdentifierUpsert


def get_asset_identity(db: Session, asset_type: str, asset_id: int) -> dict:
    models = {
        "equipment": Equipment,
        "operating_system": OperatingSystem,
        "application": Application,
        "library": Library,
    }
    model = models.get(asset_type)
    if model is None:
        raise ValueError(f"Unsupported asset type: {asset_type}.")

    asset = db.get(model, asset_id)
    if asset is None:
        raise ValueError(f"{asset_type} asset not found.")

    return {
        "asset": asset,
        "name": getattr(asset, "name", None),
        "vendor": getattr(asset, "vendor", None),
        "model": getattr(asset, "model", None),
        "version": getattr(asset, "version", None),
        "cpe": getattr(asset, "cpe", None),
        "purl": getattr(asset, "purl", None),
        "package_identifier": getattr(asset, "package_identifier", None),
        "package_manager": getattr(asset, "package_manager", None),
    }


def save_identifier_from_asset(db: Session, asset_type: str, asset_id: int) -> dict:
    identity = get_asset_identity(db, asset_type, asset_id)
    cpe = identity["cpe"]
    purl = identity["purl"]
    resolution = []
    resolved_from_nvd = False

    if not cpe and asset_type != "library":
        feed = db.scalar(
            select(Feed).where(
                Feed.feed_type == "nvd_cpe",
                Feed.enabled.is_(True),
            ).order_by(Feed.id)
        )
        if feed is not None:
            resolution = resolve_cpe(
                url=feed.url,
                vendor=identity["vendor"],
                product=identity["name"],
                model=identity["model"],
                version=identity["version"],
                timeout=feed.timeout_seconds,
                api_key=feed.api_key,
            )
            usable = [item for item in resolution if item.get("cpe") and not item.get("deprecated")]
            if usable:
                version = (identity.get("version") or "").strip().lower()
                name = (identity.get("name") or "").strip().lower().replace(" ", "_")
                ranked = sorted(
                    usable,
                    key=lambda item: (
                        0 if version and (":" + version + ":") in item["cpe"].lower() else 1,
                        0 if name and name in item["cpe"].lower() else 1,
                    ),
                )
                cpe = ranked[0]["cpe"]
                resolved_from_nvd = True

    if asset_type == "library" and not purl:
        package = identity.get("package_identifier")
        manager = identity.get("package_manager")
        name = identity.get("name")
        version = identity.get("version")
        if manager and name:
            ecosystem = {
                "npm": "npm",
                "pypi": "pypi",
                "pip": "pypi",
                "maven": "maven",
                "nuget": "nuget",
                "go": "golang",
                "cargo": "cargo",
                "rubygems": "gem",
            }.get(manager.lower())
            if ecosystem:
                purl = f"pkg:{ecosystem}/{package or name}"
                if version:
                    purl += f"@{version}"

    result = upsert_identifier(
        db,
        SecurityIdentifierUpsert(
            asset_type=asset_type,
            asset_id=asset_id,
            cpe=cpe,
            purl=purl,
            verification_status="resolved" if resolved_from_nvd else ("imported" if (cpe or purl) else "unverified"),
            confidence=90 if resolved_from_nvd else (100 if (cpe or purl) else 0),
            source="nvd_cpe_resolver" if resolved_from_nvd else "asset_record",
        ),
    )
    return {**result, "resolved_cpe": cpe, "cpe_candidates": resolution}
