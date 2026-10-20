from datetime import datetime

from pydantic import BaseModel, Field, field_validator


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


class TelegramScheduleUpdate(BaseModel):
    enabled: bool
    frequency: str = "daily"
    scan_time: str = Field(default="02:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    day_of_week: int = Field(default=0, ge=0, le=6)


class TelegramVerificationCodeRequest(BaseModel):
    api_id: str | None = Field(default=None, max_length=20)
    api_hash: str | None = Field(default=None, max_length=200)
    phone_number: str = Field(min_length=6, max_length=30)


class TelegramVerificationSubmit(BaseModel):
    challenge_id: str = Field(min_length=10, max_length=200)
    code: str = Field(min_length=3, max_length=20)
    password: str | None = Field(default=None, max_length=256)


class IntelligenceRegisterUpdate(IntelligenceUpdate):
    custom_fields: dict[str, str | None] | None = None


class IntelligenceCreate(IntelligenceUpdate):
    custom_fields: dict[str, str | None] = Field(default_factory=dict)
    cve_id: str = Field(min_length=4, max_length=30, pattern=r"^CVE-\d{4}-\d{4,}$")


class VulnerabilityCustomFieldCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    is_required: bool = False
    show_in_table: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field name cannot be empty.")
        return normalized


class VulnerabilityCustomFieldUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_required: bool | None = None
    show_in_table: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field name cannot be empty.")
        return normalized
