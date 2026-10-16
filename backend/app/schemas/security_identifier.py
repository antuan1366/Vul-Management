from datetime import datetime

from pydantic import BaseModel, Field


class SecurityIdentifierUpsert(BaseModel):
    asset_type: str = Field(min_length=1, max_length=50)
    asset_id: int = Field(gt=0)
    cpe: str | None = None
    purl: str | None = None
    verification_status: str = "unverified"
    confidence: float | None = Field(default=None, ge=0, le=100)
    source: str | None = None
    reason: str | None = None
    candidates: list[dict] | None = None
    notes: str | None = None


class SecurityIdentifierResponse(SecurityIdentifierUpsert):
    id: int
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SecurityIdentifierVerify(BaseModel):
    cpe: str | None = None
    purl: str | None = None
    notes: str | None = None
