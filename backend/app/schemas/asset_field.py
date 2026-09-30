from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


ALLOWED_FIELD_TYPES = {
    "text",
    "textarea",
    "number",
    "ip",
    "date",
    "boolean",
    "select",
    "multiselect",
    "url",
    "email",
}


class AssetFieldDefinitionBase(BaseModel):
    asset_type: str
    field_key: str
    label: str
    field_type: str
    required: bool = False
    visible: bool = True
    description: str | None = None
    description: str | None = None
    options: list[str] = Field(default_factory=list)


class AssetFieldDefinitionCreate(BaseModel):
    asset_type: str = "equipment"
    label: str
    required: bool = False
    visible: bool = True


class AssetFieldDefinitionUpdate(BaseModel):
    label: str | None = None
    required: bool | None = None
    visible: bool | None = None
    description: str | None = None
    options: list[str] | None = None


class AssetFieldDefinitionResponse(
    AssetFieldDefinitionBase
):
    id: int
    system_field: bool
    editable: bool
    deletable: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class AssetFieldValueInput(BaseModel):
    field_key: str
    value: Any = None