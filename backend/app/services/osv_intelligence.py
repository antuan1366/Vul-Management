import json

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feed import Feed
from app.services.vulnerability_candidates import upsert_candidate
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
        parsed = {
            "cve_id": cve_id,
            "source": "osv",
            "description": item.get("details") or item.get("summary"),
            "references": json.dumps(item.get("references") or [], ensure_ascii=False),
            "published_at": _parse_datetime(item.get("published")),
            "modified_at": _parse_datetime(item.get("modified")),
            "affected_product": json.dumps(affected, ensure_ascii=False),
            "affected_versions": json.dumps(affected, ensure_ascii=False),
        }

        candidate = upsert_candidate(
            db,
            parsed=parsed,
            asset_type=asset_type,
            asset_id=asset_id,
            match_status="confirmed_affected",
            match_method="osv_purl",
            confidence=96,
        )
        if candidate.review_status == "pending":
            linked += 1
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
