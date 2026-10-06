from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security_identifier import SecurityIdentifier
from app.schemas.security_identifier import SecurityIdentifierUpsert


def get_identifier(
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


def upsert_identifier(
    db: Session,
    data: SecurityIdentifierUpsert,
) -> SecurityIdentifier:
    identifier = get_identifier(db, data.asset_type, data.asset_id)

    if identifier is None:
        identifier = SecurityIdentifier(
            asset_type=data.asset_type,
            asset_id=data.asset_id,
        )
        db.add(identifier)

    for key, value in data.model_dump().items():
        setattr(identifier, key, value)

    db.commit()
    db.refresh(identifier)
    return identifier
