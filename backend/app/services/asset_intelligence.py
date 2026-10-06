import json
from datetime import datetime
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.equipment import Equipment
from app.models.feed import Feed
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.models.security_identifier_check import SecurityIdentifierCheck
from app.services.cpe_resolver import resolve_cpe
from app.services.security_identifiers import upsert_identifier
from app.schemas.security_identifier import SecurityIdentifierUpsert


MODELS = {
    "equipment": Equipment,
    "operating_system": OperatingSystem,
    "application": Application,
    "library": Library,
}


def get_asset_identity(db: Session, asset_type: str, asset_id: int) -> dict:
    model = MODELS.get(asset_type)
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


def _purl_for_library(identity: dict) -> tuple[str | None, str | None]:
    existing = identity.get("purl")
    if existing and existing.startswith("pkg:"):
        return existing, None

    manager = (identity.get("package_manager") or "").strip().lower()
    name = (identity.get("package_identifier") or identity.get("name") or "").strip()
    version = (identity.get("version") or "").strip()

    ecosystem = {
        "npm": "npm",
        "node": "npm",
        "nodejs": "npm",
        "pypi": "pypi",
        "pip": "pypi",
        "maven": "maven",
        "nuget": "nuget",
        "go": "golang",
        "golang": "golang",
        "cargo": "cargo",
        "rust": "cargo",
        "rubygems": "gem",
        "gem": "gem",
        "composer": "composer",
    }.get(manager)

    if not ecosystem:
        return None, "Package manager is missing or unsupported."
    if not name:
        return None, "Library/package name is missing."

    purl_name = quote(name, safe="@/._-~")
    purl = f"pkg:{ecosystem}/{purl_name}"
    if version:
        purl += f"@{quote(version, safe='._-+~')}"
    return purl, None


def _missing_fields(asset_type: str, identity: dict) -> list[str]:
    if asset_type == "library":
        fields = ["name", "version", "package_manager"]
    else:
        fields = ["vendor", "version"]
        fields.append("model" if asset_type == "equipment" else "name")

    return [
        field
        for field in fields
        if not str(identity.get(field) or "").strip()
    ]


def _save_check(db: Session, asset_type: str, asset_id: int, result: dict) -> None:
    db.add(
        SecurityIdentifierCheck(
            asset_type=asset_type,
            asset_id=asset_id,
            status=result["status"],
            cpe=result.get("cpe"),
            purl=result.get("purl"),
            confidence=result.get("confidence"),
            source=result.get("source"),
            reason=result.get("reason"),
            candidates=json.dumps(
                result.get("candidates") or [],
                ensure_ascii=False,
            ),
            checked_at=datetime.utcnow(),
        )
    )


def _identifier_result(db: Session, asset_type: str, asset_id: int) -> dict:
    identity = get_asset_identity(db, asset_type, asset_id)
    missing = _missing_fields(asset_type, identity)

    if missing:
        result = {
            "status": "insufficient_data",
            "cpe": None,
            "purl": None,
            "confidence": 0,
            "source": None,
            "reason": "Missing required information: " + ", ".join(missing) + ".",
            "candidates": [],
        }
        upsert_identifier(
            db,
            SecurityIdentifierUpsert(
                asset_type=asset_type,
                asset_id=asset_id,
                verification_status=result["status"],
                confidence=0,
                source=None,
                reason=result["reason"],
                candidates=[],
            ),
        )
        _save_check(db, asset_type, asset_id, result)
        db.commit()
        return result

    if asset_type == "library":
        purl, reason = _purl_for_library(identity)
        if reason:
            result = {
                "status": "insufficient_data",
                "cpe": None,
                "purl": None,
                "confidence": 0,
                "source": "purl",
                "reason": reason,
                "candidates": [],
            }
        else:
            result = {
                "status": "pending_verification",
                "cpe": None,
                "purl": purl,
                "confidence": 100,
                "source": "purl_generated",
                "reason": "PURL generated from package metadata. Verify before vulnerability discovery.",
                "candidates": [],
            }

        upsert_identifier(
            db,
            SecurityIdentifierUpsert(
                asset_type=asset_type,
                asset_id=asset_id,
                purl=result.get("purl"),
                verification_status=result["status"],
                confidence=result["confidence"],
                source=result["source"],
                reason=result["reason"],
                candidates=[],
            ),
        )
        _save_check(db, asset_type, asset_id, result)
        db.commit()
        return result

    feed = db.scalar(
        select(Feed)
        .where(Feed.feed_type == "nvd_cpe", Feed.enabled.is_(True))
        .order_by(Feed.id)
    )

    if feed is None:
        result = {
            "status": "feed_unavailable",
            "cpe": None,
            "purl": None,
            "confidence": 0,
            "source": "nvd_cpe",
            "reason": "No enabled NVD CPE feed is configured. Check Administration > Feeds.",
            "candidates": [],
        }
        upsert_identifier(
            db,
            SecurityIdentifierUpsert(
                asset_type=asset_type,
                asset_id=asset_id,
                verification_status=result["status"],
                confidence=0,
                source="nvd_cpe",
                reason=result["reason"],
                candidates=[],
            ),
        )
        _save_check(db, asset_type, asset_id, result)
        db.commit()
        return result

    product = identity.get("model") if asset_type == "equipment" else identity.get("name")

    try:
        candidates = resolve_cpe(
            url=feed.url,
            vendor=identity.get("vendor"),
            product=product,
            model=identity.get("model"),
            version=identity.get("version"),
            timeout=feed.timeout_seconds,
            api_key=feed.api_key,
        )
    except Exception as error:
        result = {
            "status": "error",
            "cpe": None,
            "purl": None,
            "confidence": 0,
            "source": "nvd_cpe",
            "reason": f"NVD CPE lookup failed: {error.__class__.__name__}.",
            "candidates": [],
        }
        upsert_identifier(
            db,
            SecurityIdentifierUpsert(
                asset_type=asset_type,
                asset_id=asset_id,
                verification_status=result["status"],
                confidence=0,
                source="nvd_cpe",
                reason=result["reason"],
                candidates=[],
            ),
        )
        _save_check(db, asset_type, asset_id, result)
        db.commit()
        return result

    candidates = [item for item in candidates if not item.get("deprecated")]

    if not candidates:
        result = {
            "status": "not_found",
            "cpe": None,
            "purl": None,
            "confidence": 0,
            "source": "nvd_cpe",
            "reason": "No matching CPE was found in the NVD CPE catalog for the supplied asset information.",
            "candidates": [],
        }
    elif len(candidates) == 1 or candidates[0].get("score", 0) >= candidates[1].get("score", 0) + 20:
        confidence = min(99, max(60, candidates[0].get("score", 0)))
        result = {
            "status": "pending_verification",
            "cpe": candidates[0]["cpe"],
            "purl": None,
            "confidence": confidence,
            "source": "nvd_cpe",
            "reason": "A likely CPE was found. Administrator verification is required.",
            "candidates": candidates[:10],
        }
    else:
        result = {
            "status": "multiple_matches",
            "cpe": candidates[0]["cpe"],
            "purl": None,
            "confidence": max(50, min(89, candidates[0].get("score", 0))),
            "source": "nvd_cpe",
            "reason": "Multiple CPE candidates matched. Administrator must select and verify the correct CPE.",
            "candidates": candidates[:10],
        }

    upsert_identifier(
        db,
        SecurityIdentifierUpsert(
            asset_type=asset_type,
            asset_id=asset_id,
            cpe=result.get("cpe"),
            verification_status=result["status"],
            confidence=result["confidence"],
            source=result["source"],
            reason=result["reason"],
            candidates=result.get("candidates", []),
        ),
    )
    _save_check(db, asset_type, asset_id, result)
    db.commit()
    return result


def save_identifier_from_asset(db: Session, asset_type: str, asset_id: int) -> dict:
    return _identifier_result(db, asset_type, asset_id)


def check_all_assets(db: Session, asset_type: str) -> dict:
    model = MODELS.get(asset_type)
    if model is None:
        raise ValueError(f"Unsupported asset type: {asset_type}.")

    assets = db.scalars(select(model).order_by(model.id)).all()
    results = []

    for asset in assets:
        try:
            result = _identifier_result(db, asset_type, asset.id)
            results.append(
                {
                    "asset_id": asset.id,
                    "asset_name": getattr(asset, "name", None)
                    or getattr(asset, "model", None)
                    or f"{asset_type} #{asset.id}",
                    "status": result.get("status"),
                    "cpe": result.get("cpe"),
                    "purl": result.get("purl"),
                    "confidence": result.get("confidence"),
                    "reason": result.get("reason"),
                }
            )
        except Exception as error:
            results.append(
                {
                    "asset_id": asset.id,
                    "asset_name": getattr(asset, "name", None) or f"{asset_type} #{asset.id}",
                    "status": "error",
                    "cpe": None,
                    "purl": None,
                    "confidence": 0,
                    "reason": f"Unexpected error: {error.__class__.__name__}.",
                }
            )

    return {
        "asset_type": asset_type,
        "total": len(results),
        "resolved": sum(1 for item in results if item.get("cpe") or item.get("purl")),
        "verified": sum(1 for item in results if item.get("status") == "verified"),
        "pending_verification": sum(
            1
            for item in results
            if item.get("status") in {"pending_verification", "multiple_matches"}
        ),
        "not_found": sum(1 for item in results if item.get("status") == "not_found"),
        "results": results,
    }
