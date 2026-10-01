import json

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feed import Feed
from app.models.vulnerability import AssetVulnerability, Vulnerability
from app.services.vulnerability_intelligence import _parse_datetime


def sync_osv_for_purl(
    db: Session,
    feed: Feed,
    *,
    purl: str,
    asset_type: str,
    asset_id: int,
) -> dict:
    headers = {
        "User-Agent": "Vul-Management/1.2",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if feed.auth_type == "api_key" and feed.api_key:
        headers["apiKey"] = feed.api_key
    elif feed.auth_type == "bearer" and feed.api_key:
        headers["Authorization"] = f"Bearer {feed.api_key}"

    response = httpx.post(
        feed.url,
        json={"package": {"purl": purl}},
        headers=headers,
        timeout=feed.timeout_seconds,
        follow_redirects=True,
    )
    response.raise_for_status()
    data = response.json()

    linked = 0
    created = 0

    for item in data.get("vulns", []):
        aliases = item.get("aliases") or []
        cve_id = next(
            (value for value in aliases if value.startswith("CVE-")),
            item.get("id"),
        )
        if not cve_id:
            continue

        affected = item.get("affected") or []
        vulnerability = db.scalar(
            select(Vulnerability).where(Vulnerability.cve_id == cve_id)
        )

        values = {
            "cve_id": cve_id,
            "source": "osv",
            "description": item.get("details") or item.get("summary"),
            "references": json.dumps(item.get("references") or [], ensure_ascii=False),
            "published_at": _parse_datetime(item.get("published")),
            "modified_at": _parse_datetime(item.get("modified")),
            "affected_product": json.dumps(affected, ensure_ascii=False),
            "affected_versions": json.dumps(affected, ensure_ascii=False),
        }

        if vulnerability is None:
            vulnerability = Vulnerability(**values)
            db.add(vulnerability)
            db.flush()
            created += 1
        else:
            for key, value in values.items():
                if value is not None:
                    setattr(vulnerability, key, value)

        mapping = db.scalar(
            select(AssetVulnerability).where(
                AssetVulnerability.asset_type == asset_type,
                AssetVulnerability.asset_id == asset_id,
                AssetVulnerability.vulnerability_id == vulnerability.id,
            )
        )
        if mapping is None:
            db.add(
                AssetVulnerability(
                    asset_type=asset_type,
                    asset_id=asset_id,
                    vulnerability_id=vulnerability.id,
                    match_status="confirmed_affected",
                    match_method="osv_purl",
                    confidence=96,
                )
            )
        else:
            mapping.match_status = "confirmed_affected"
            mapping.match_method = "osv_purl"
            mapping.confidence = 96
        linked += 1

    db.commit()
    return {
        "asset_type": asset_type,
        "asset_id": asset_id,
        "purl": purl,
        "returned_vulnerabilities": len(data.get("vulns", [])),
        "linked_vulnerabilities": linked,
        "created_vulnerabilities": created,
    }
