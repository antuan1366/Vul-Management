from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


FEED_TYPES = {"nvd_cpe", "nvd_cve", "cisa_kev", "osv", "custom"}
AUTH_TYPES = {"none", "api_key", "bearer"}
METHODS = {"GET", "POST"}


class FeedCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    feed_type: str
    url: HttpUrl
    method: str = "GET"
    enabled: bool = True
    auth_type: str = "none"
    api_key: str | None = None
    timeout_seconds: int = Field(default=15, ge=3, le=120)
    description: str | None = None


class FeedUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    feed_type: str | None = None
    url: HttpUrl | None = None
    method: str | None = None
    enabled: bool | None = None
    auth_type: str | None = None
    api_key: str | None = None
    clear_api_key: bool = False
    timeout_seconds: int | None = Field(default=None, ge=3, le=120)
    description: str | None = None


class FeedResponse(BaseModel):
    id: int
    name: str
    feed_type: str
    url: str
    method: str
    enabled: bool
    auth_type: str
    has_api_key: bool
    timeout_seconds: int
    description: str | None
    last_test_status: str | None
    last_test_message: str | None
    last_test_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
