from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.security_identifier import (
    SecurityIdentifierResponse,
    SecurityIdentifierUpsert,
    SecurityIdentifierVerify,
)
from app.services.security_identifiers import get_identifier, list_identifiers, upsert_identifier


router = APIRouter(
    prefix="/api/security-identifiers",
    tags=["Security Identifiers"],
)


@router.get("")
def list_security_identifiers_api(
    asset_type: str,
    db: Session = Depends(get_db),
):
    return list_identifiers(db, asset_type)


@router.get("/{asset_type}/{asset_id}", response_model=SecurityIdentifierResponse)
def get_security_identifier_api(
    asset_type: str,
    asset_id: int,
    db: Session = Depends(get_db),
):
    identifier = get_identifier(db, asset_type, asset_id)
    if identifier is None:
        raise HTTPException(status_code=404, detail="Security identifier not found.")
    return identifier


@router.post("/{asset_type}/{asset_id}/verify", response_model=SecurityIdentifierResponse)
def verify_security_identifier_api(
    asset_type: str,
    asset_id: int,
    data: SecurityIdentifierVerify,
    db: Session = Depends(get_db),
):
    payload = SecurityIdentifierUpsert(
        asset_type=asset_type,
        asset_id=asset_id,
        cpe=data.cpe,
        purl=data.purl,
        verification_status="verified",
        confidence=100,
        source="administrator",
        reason="Verified by administrator.",
        candidates=[],
        notes=data.notes,
    )
    return upsert_identifier(db, payload)


@router.put("", response_model=SecurityIdentifierResponse)
def upsert_security_identifier_api(
    data: SecurityIdentifierUpsert,
    db: Session = Depends(get_db),
):
    return upsert_identifier(db, data)
