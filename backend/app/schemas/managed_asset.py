from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ManagedAssetBase(BaseModel):
    name: str | None = None
    equipment_id: int | None = None
    vendor: str | None = None
    version: str | None = None
    edition: str | None = None
    build: str | None = None
    architecture: str | None = None
    kernel: str | None = None
    cpe: str | None = None
    install_date: str | None = None
    support_end_date: str | None = None
    lifecycle_status: str | None = None
    platform: str | None = None
    install_path: str | None = None
    owner: str | None = None
    criticality: str | None = None
    environment: str | None = None
    language: str | None = None
    package_manager: str | None = None
    package_identifier: str | None = None
    purl: str | None = None
    repository: str | None = None
    description: str | None = None


class ManagedAssetCreate(ManagedAssetBase):
    custom_fields: dict[str, Any] = {}


class ManagedAssetUpdate(ManagedAssetBase):
    custom_fields: dict[str, Any] = {}


class ManagedAssetResponse(ManagedAssetBase):
    id: int
    custom_fields: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
