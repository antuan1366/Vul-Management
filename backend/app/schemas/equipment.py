from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EquipmentBase(BaseModel):
    name: str
    device_type: str | None = None
    vendor: str | None = None
    model: str | None = None
    version: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    cpe: str | None = None
    criticality: str = "Medium"
    environment: str = "Production"
    description: str | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: str | None = None
    device_type: str | None = None
    vendor: str | None = None
    model: str | None = None
    version: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    cpe: str | None = None
    criticality: str | None = None
    environment: str | None = None
    description: str | None = None


class EquipmentResponse(EquipmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )