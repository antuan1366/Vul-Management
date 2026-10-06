from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vulnerability import AssetVulnerability

router = APIRouter(prefix="/api/remediation", tags=["Remediation"])


class RemediationUpdate(BaseModel):
    analyst_status: str = Field(min_length=1, max_length=30)
    notes: str | None = None


@router.put("/{mapping_id}")
def update_remediation(mapping_id: int, data: RemediationUpdate, db: Session = Depends(get_db)):
    mapping = db.get(AssetVulnerability, mapping_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="Asset vulnerability mapping not found.")

    allowed = {"open", "in_progress", "mitigated", "patched", "accepted", "false_positive", "closed"}
    if data.analyst_status not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported remediation status.")

    mapping.analyst_status = data.analyst_status
    mapping.notes = data.notes
    db.commit()
    db.refresh(mapping)
    return mapping


@router.get("")
def list_remediation(status: str | None = None, db: Session = Depends(get_db)):
    query = select(AssetVulnerability)
    if status:
        query = query.where(AssetVulnerability.analyst_status == status)
    return db.scalars(query.order_by(AssetVulnerability.last_seen_at.desc())).all()
