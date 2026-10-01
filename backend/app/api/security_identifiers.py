from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.security_identifier import (
    SecurityIdentifierResponse,
    SecurityIdentifierUpsert,
)
from app.services.security_identifiers import get_identifier, upsert_identifier


router = APIRouter(
    prefix="/api/security-identifiers",
    tags=["Security Identifiers"],
)


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


@router.put("", response_model=SecurityIdentifierResponse)
def upsert_security_identifier_api(
    data: SecurityIdentifierUpsert,
    db: Session = Depends(get_db),
):
    return upsert_identifier(db, data)
