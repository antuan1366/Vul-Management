from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserCreate


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    next: str | None = Field(default=None, max_length=512)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class InitialAdminSetup(UserCreate):
    pass
