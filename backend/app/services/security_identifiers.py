import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security_identifier import SecurityIdentifier
from app.schemas.security_identifier import SecurityIdentifierUpsert


def _serialize(identifier: SecurityIdentifier) -> dict:
    candidates = []
    if identifier.candidates:
        try:
            candidates = json.loads(identifier.candidates)
        except json.JSONDecodeError:
            candidates = []

    return {
        "id": identifier.id,
        "asset_type": identifier.asset_type,
        "asset_id": identifier.asset_id,
        "cpe": identifier.cpe,
        "purl": identifier.purl,
        "verification_status": identifier.verification_status,
        "confidence": identifier.confidence,
        "source": identifier.source,
        "reason": identifier.reason,
        "candidates": candidates,
        "last_checked_at": identifier.last_checked_at,
        "notes": identifier.notes,
        "created_at": identifier.created_at,
        "updated_at": identifier.updated_at,
    }


def get_identifier(
    db: Session,
    asset_type: str,
    asset_id: int,
) -> dict | None:
    identifier = db.scalar(
        select(SecurityIdentifier).where(
            SecurityIdentifier.asset_type == asset_type,
            SecurityIdentifier.asset_id == asset_id,
        )
    )
    return _serialize(identifier) if identifier else None


def get_identifier_model(
    db: Session,
    asset_type: str,
    asset_id: int,
) -> SecurityIdentifier | None:
    return db.scalar(
        select(SecurityIdentifier).where(
            SecurityIdentifier.asset_type == asset_type,
            SecurityIdentifier.asset_id == asset_id,
        )
    )


def list_identifiers(db: Session, asset_type: str) -> list[dict]:
    identifiers = db.scalars(
        select(SecurityIdentifier)
        .where(SecurityIdentifier.asset_type == asset_type)
        .order_by(SecurityIdentifier.asset_id)
    ).all()
    return [_serialize(identifier) for identifier in identifiers]


def upsert_identifier(
    db: Session,
    data: SecurityIdentifierUpsert,
) -> dict:
    identifier = get_identifier_model(db, data.asset_type, data.asset_id)

    if identifier is None:
        identifier = SecurityIdentifier(
            asset_type=data.asset_type,
            asset_id=data.asset_id,
        )
        db.add(identifier)

    values = data.model_dump()
    candidates = values.pop("candidates", None)

    for key, value in values.items():
        setattr(identifier, key, value)

    if candidates is not None:
        identifier.candidates = json.dumps(candidates, ensure_ascii=False)

    identifier.last_checked_at = datetime.utcnow()
    db.commit()
    db.refresh(identifier)
    return _serialize(identifier)
