from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["admin", "user"] = "user"
    is_active: bool = True

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=12, max_length=128)
    role: Literal["admin", "user"] | None = None
    is_active: bool | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    role: Literal["admin", "user"]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
