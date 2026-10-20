"""Heuristic matching of public threat-intelligence messages against inventory assets.

Matches are advisory only: an asset name/vendor appearing in a source message does
not prove that the asset is affected by the referenced CVE.
"""

import re
import unicodedata
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.asset_field import AssetFieldDefinition, AssetFieldValue
from app.models.equipment import Equipment
from app.models.library import Library
from app.models.operating_system import OperatingSystem


ASSET_MODELS = (
    ("equipment", "Equipment", Equipment, (
        "name", "device_type", "vendor", "model", "ip_address", "serial_number", "cpe",
    )),
    ("operating_system", "Operating System", OperatingSystem, (
        "name", "vendor", "cpe", "edition", "build", "kernel",
    )),
    ("application", "Application", Application, (
        "name", "vendor", "cpe", "install_path", "platform",
    )),
    ("library", "Library", Library, (
        "name", "vendor", "purl", "package_identifier", "repository", "cpe",
    )),
)

GENERIC_TERMS = {
    "a", "an", "the", "and", "or", "for", "with", "from", "to",
    "server", "servers", "network", "networks", "system", "systems",
    "software", "hardware", "application", "applications", "device", "devices",
    "asset", "assets", "product", "products", "platform", "platforms",
    "production", "prod", "test", "testing", "development", "dev", "staging",
    "critical", "high", "medium", "low", "unknown", "none", "null",
    "active", "inactive", "enabled", "disabled", "true", "false",
    "yes", "no", "other", "general", "default", "cpe", "purl", "database",
}

NON_IDENTIFYING_CUSTOM_KEYS = {
    "description", "notes", "comment", "comments", "remark", "remarks",
    "criticality", "environment", "lifecycle_status", "status", "state",
    "install_date", "support_end_date", "created_at", "updated_at",
    "version", "firmware", "revision", "release", "build", "edition",
    "architecture", "language", "package_manager",
}

FIELD_LABELS = {
    "name": "Name",
    "device_type": "Device Type",
    "vendor": "Vendor / Brand",
    "model": "Model",
    "ip_address": "IP Address",
    "serial_number": "Serial Number",
    "cpe": "CPE",
    "edition": "Edition",
    "build": "Build",
    "kernel": "Kernel",
    "install_path": "Install Path",
    "platform": "Platform",
    "purl": "Package URL",
    "package_identifier": "Package Identifier",
    "repository": "Repository",
}


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _is_useful_term(term: str) -> bool:
    if not term or term in GENERIC_TERMS:
        return False
    if len(term) < 2:
        return False
    tokens = term.split()
    if len(tokens) > 1 and all(token.isdigit() or token in {"a", "o", "h", "p", "v", "x"} for token in tokens):
        return False
    if term.isdigit():
        # A bare product/version number is too common unless it is long enough
        # to act as a real model/build identifier.
        return len(term) >= 4
    if len(term) == 2 and term not in {"hp"} and not any(char.isdigit() for char in term):
        return False
    return True


def _term_variants(value: Any) -> list[str]:
    raw = str(value or "").strip()
    if not raw or len(raw) > 500:
        return []
    normalized = _normalize(raw)
    if not normalized:
        return []

    variants: list[str] = []
    if _is_useful_term(normalized):
        variants.append(normalized)

    # A field such as "Cisco Systems Inc." should also match a message that
    # mentions only "Cisco". Ignore generic tokens to reduce false positives.
    for token in normalized.split():
        if _is_useful_term(token) and token not in variants:
            variants.append(token)

    # CPEs and package URLs are often written with different separators in
    # advisories. Their identifier components are useful aliases as well.
    for component in re.split(r"[:/@#]", raw):
        normalized_component = _normalize(component)
        if _is_useful_term(normalized_component) and normalized_component not in variants:
            variants.append(normalized_component)
        for token in normalized_component.split():
            if _is_useful_term(token) and token not in variants:
                variants.append(token)

    return variants


def _asset_display_name(asset: Any, model_fields: tuple[str, ...], asset_type: str, asset_id: int) -> str:
    name = str(getattr(asset, "name", "") or "").strip()
    if name:
        return name
    vendor = str(getattr(asset, "vendor", "") or "").strip()
    model = str(getattr(asset, "model", "") or "").strip()
    combined = " ".join(part for part in (vendor, model) if part)
    return combined or f"{asset_type.replace('_', ' ').title()} #{asset_id}"


def build_asset_match_index(db: Session) -> list[dict[str, Any]]:
    """Build an in-memory index from currently registered inventory records."""
    assets: dict[tuple[str, int], dict[str, Any]] = {}

    for asset_type, type_label, model, field_keys in ASSET_MODELS:
        for asset in db.scalars(select(model)).all():
            asset_id = int(asset.id)
            entry = {
                "asset_id": asset_id,
                "asset_type": asset_type,
                "asset_type_label": type_label,
                "asset_name": _asset_display_name(asset, field_keys, asset_type, asset_id),
                "terms": defaultdict(set),
            }
            assets[(asset_type, asset_id)] = entry

            for field_key in field_keys:
                value = getattr(asset, field_key, None)
                for term in _term_variants(value):
                    entry["terms"][term].add(FIELD_LABELS.get(field_key, field_key.replace("_", " ").title()))

    custom_values = db.execute(
        select(
            AssetFieldValue.asset_type,
            AssetFieldValue.asset_id,
            AssetFieldDefinition.field_key,
            AssetFieldDefinition.label,
            AssetFieldValue.value,
        )
        .join(AssetFieldDefinition, AssetFieldDefinition.id == AssetFieldValue.field_id)
        .where(
            AssetFieldDefinition.system_field.is_(False),
            AssetFieldValue.value.is_not(None),
        )
    ).all()

    for asset_type, raw_asset_id, field_key, label, value in custom_values:
        entry = assets.get((str(asset_type), int(raw_asset_id)))
        if entry is None:
            continue
        key = _normalize(field_key).replace(" ", "_")
        normalized_label = _normalize(label).replace(" ", "_")
        label_words = set(normalized_label.split("_"))
        non_identifying_label = (
            normalized_label in NON_IDENTIFYING_CUSTOM_KEYS
            or bool(label_words.intersection(NON_IDENTIFYING_CUSTOM_KEYS))
        )
        if key in NON_IDENTIFYING_CUSTOM_KEYS or non_identifying_label:
            continue
        display_label = str(label or field_key or "Custom Field")
        for term in _term_variants(value):
            entry["terms"][term].add(display_label)

    # Avoid loading empty index entries and turn sets into deterministic data.
    indexed = []
    for entry in assets.values():
        terms = {
            term: sorted(labels)
            for term, labels in entry["terms"].items()
        }
        if terms:
            indexed.append({
                "asset_id": entry["asset_id"],
                "asset_type": entry["asset_type"],
                "asset_type_label": entry["asset_type_label"],
                "asset_name": entry["asset_name"],
                "terms": terms,
            })
    return indexed


def match_message_to_assets(message_text: str | None, index: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the assets whose identifying phrases occur in the source message."""
    normalized_message = _normalize(message_text)
    if not normalized_message or not index:
        return {"matched": False, "asset_match_count": 0, "asset_matches": []}

    padded_message = f" {normalized_message} "
    matches: list[dict[str, Any]] = []

    for asset in index:
        matched_terms = []
        for term, labels in asset["terms"].items():
            if f" {term} " in padded_message:
                matched_terms.append({
                    "term": term,
                    "fields": labels,
                })
        if not matched_terms:
            continue

        matched_terms.sort(key=lambda item: (-len(item["term"]), item["term"]))
        matches.append({
            "asset_id": asset["asset_id"],
            "asset_type": asset["asset_type"],
            "asset_type_label": asset["asset_type_label"],
            "asset_name": asset["asset_name"],
            "matched_terms": matched_terms[:8],
        })

    matches.sort(key=lambda item: (item["asset_type_label"], item["asset_name"].casefold(), item["asset_id"]))
    return {
        "matched": bool(matches),
        "asset_match_count": len(matches),
        # Bound the response size while preserving the total matching-asset count.
        "asset_matches": matches[:10],
    }


def annotate_scan_results_with_asset_matches(
    db: Session,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach an advisory asset-match indicator to serialized Scan Result rows."""
    if not records:
        return records

    index = build_asset_match_index(db)
    for record in records:
        record["asset_match"] = match_message_to_assets(record.get("message_text"), index)
    return records
