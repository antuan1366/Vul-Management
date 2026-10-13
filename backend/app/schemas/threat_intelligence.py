from datetime import datetime

from pydantic import BaseModel, Field


class TelegramFeedCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    channel_username: str = Field(min_length=1, max_length=150)
    enabled: bool = True


class TelegramFeedUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    channel_username: str | None = Field(default=None, min_length=1, max_length=150)
    enabled: bool | None = None


class TelegramScanRequest(BaseModel):
    mode: str = "new"
    start_date: datetime | None = None


class ReviewRequest(BaseModel):
    status: str
    notes: str | None = None


class IntelligenceUpdate(BaseModel):
    severity: str | None = None
    cvss_score: float | None = None
    affected_product: str | None = None
    affected_versions: str | None = None
    remediation: str | None = None
    mitigation: str | None = None
    description: str | None = None
    references_text: str | None = None
