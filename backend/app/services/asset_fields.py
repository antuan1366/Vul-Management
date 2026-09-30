import json
import re
from datetime import date
from ipaddress import ip_address

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_field import (
    AssetFieldDefinition,
    AssetFieldValue,
)
from app.schemas.asset_field import (
    ALLOWED_FIELD_TYPES,
    AssetFieldDefinitionCreate,
    AssetFieldDefinitionUpdate,
)


DEFAULT_EQUIPMENT_FIELDS = [
    {
        "field_key": "name",
        "label": "Name",
        "field_type": "text",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Primary asset name.",
    },
    {
        "field_key": "device_type",
        "label": "Device Type",
        "field_type": "text",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Equipment type.",
    },
    {
        "field_key": "vendor",
        "label": "Vendor",
        "field_type": "text",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Equipment vendor.",
    },
    {
        "field_key": "model",
        "label": "Model",
        "field_type": "text",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Equipment model.",
    },
    {
        "field_key": "version",
        "label": "Version / Firmware",
        "field_type": "text",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Firmware or software version.",
    },
    {
        "field_key": "ip_address",
        "label": "IP Address",
        "field_type": "ip",
        "required": False,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Management or primary IP address.",
    },
    {
        "field_key": "serial_number",
        "label": "Serial Number",
        "field_type": "text",
        "required": False,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Hardware serial number.",
    },
    {
        "field_key": "cpe",
        "label": "CPE",
        "field_type": "text",
        "required": False,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Common Platform Enumeration identifier.",
    },
    {
        "field_key": "criticality",
        "label": "Criticality",
        "field_type": "select",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "options": [
            "Critical",
            "High",
            "Medium",
            "Low",
        ],
        "description": "Business/security criticality.",
    },
    {
        "field_key": "environment",
        "label": "Environment",
        "field_type": "select",
        "required": True,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "options": [
            "Production",
            "DR",
            "Test",
            "Development",
        ],
        "description": "Deployment environment.",
    },
    {
        "field_key": "description",
        "label": "Description",
        "field_type": "textarea",
        "required": False,
        "visible": True,
        "system_field": True,
        "editable": True,
        "deletable": False,
        "description": "Additional information.",
    },
]


def _serialize_options(options: list[str]) -> str | None:
    if not options:
        return None

    return json.dumps(
        options,
        ensure_ascii=False,
    )


def _deserialize_options(
    options: str | None,
) -> list[str]:
    if not options:
        return []

    try:
        value = json.loads(options)

        if isinstance(value, list):
            return [
                str(item)
                for item in value
            ]

    except json.JSONDecodeError:
        pass

    return []


def serialize_field(field):
    return {
        "id": field.id,
        "asset_type": field.asset_type,
        "field_key": field.field_key,
        "label": field.label,
        "field_type": field.field_type,
        "required": field.required,
        "visible": field.visible,
        "system_field": field.system_field,
        "editable": field.editable,
        "deletable": field.deletable,
        "description": field.description,
        "options": _deserialize_options(
            field.options
        ),
        "created_at": field.created_at,
        "updated_at": field.updated_at,
    }


def seed_default_fields(db: Session) -> None:
    existing_fields = list(
        db.scalars(
            select(AssetFieldDefinition).where(
                AssetFieldDefinition.asset_type
                == "equipment"
            )
        ).all()
    )

    existing_keys = {
        field.field_key
        for field in existing_fields
    }

    changed = False

    for definition in DEFAULT_EQUIPMENT_FIELDS:

        if definition["field_key"] in existing_keys:
            continue

        field = AssetFieldDefinition(
            asset_type="equipment",
            field_key=definition["field_key"],
            label=definition["label"],
            field_type=definition["field_type"],
            required=definition["required"],
            visible=definition["visible"],
            system_field=definition["system_field"],
            editable=definition["editable"],
            deletable=definition["deletable"],
            options=_serialize_options(
                definition.get("options", [])
            ),
            description=definition.get(
                "description"
            ),
        )

        db.add(field)
        changed = True

    if changed:
        db.commit()


def get_asset_fields(
    db: Session,
    asset_type: str,
):
    fields = list(
        db.scalars(
            select(AssetFieldDefinition)
            .where(
                AssetFieldDefinition.asset_type
                == asset_type
            )
            .order_by(
                AssetFieldDefinition.id
            )
        ).all()
    )

    return [
        serialize_field(field)
        for field in fields
    ]


def get_asset_field(
    db: Session,
    field_id: int,
):
    return db.get(
        AssetFieldDefinition,
        field_id,
    )


def _generate_field_key(
    db: Session,
    asset_type: str,
    label: str,
) -> str:
    key = re.sub(
        r"[^a-z0-9]+",
        "_",
        label.lower().strip(),
    ).strip("_")

    if not key:
        key = "custom_field"

    if not key[0].isalpha():
        key = f"field_{key}"

    base_key = key
    counter = 2

    while db.scalar(
        select(AssetFieldDefinition).where(
            AssetFieldDefinition.asset_type == asset_type,
            AssetFieldDefinition.field_key == key,
        )
    ):
        key = f"{base_key}_{counter}"
        counter += 1

    return key


def create_asset_field(
    db: Session,
    field_data: AssetFieldDefinitionCreate,
):
    field_key = _generate_field_key(
        db=db,
        asset_type=field_data.asset_type,
        label=field_data.label,
    )

    existing = db.scalar(
        select(AssetFieldDefinition).where(
            AssetFieldDefinition.asset_type
            == field_data.asset_type,
            AssetFieldDefinition.field_key
            == field_key,
        )
    )

    if existing:
        raise ValueError(
            "A field with this key already exists."
        )

    field = AssetFieldDefinition(
        asset_type=field_data.asset_type,
        field_key=field_key,
        label=field_data.label,
        field_type="text",
        required=field_data.required,
        visible=field_data.visible,
        system_field=False,
        editable=True,
        deletable=True,
        options=None,
        description=field_data.description,
    )

    db.add(field)
    db.commit()
    db.refresh(field)

    return serialize_field(field)


def update_asset_field(
    db: Session,
    field: AssetFieldDefinition,
    field_data: AssetFieldDefinitionUpdate,
):
    if not field.editable:
        raise ValueError(
            "This field cannot be edited."
        )

    update_data = field_data.model_dump(
        exclude_unset=True
    )

    if "label" in update_data:
        field.label = update_data["label"]

    if "required" in update_data:
        field.required = update_data["required"]

    if "visible" in update_data:
        field.visible = update_data["visible"]

    if "description" in update_data:
        field.description = update_data[
            "description"
        ]

    if "options" in update_data:
        field.options = _serialize_options(
            update_data["options"]
        )

    db.commit()
    db.refresh(field)

    return serialize_field(field)


def delete_asset_field(
    db: Session,
    field: AssetFieldDefinition,
):
    if not field.deletable:
        raise ValueError(
            "This field cannot be deleted."
        )

    db.delete(field)

    db.execute(
        AssetFieldValue.__table__.delete().where(
            AssetFieldValue.field_id
            == field.id
        )
    )

    db.commit()


def _normalize_value(
    field: AssetFieldDefinition,
    value,
):
    if value is None:
        return None

    field_type = field.field_type

    if field_type in {
        "text",
        "textarea",
        "url",
        "email",
        "ip",
        "date",
        "select",
    }:
        value = str(value).strip()

        if not value:
            return None

    if field_type == "number":
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Field '{field.label}' must be a number."
            )

        return str(number)

    if field_type == "boolean":
        if isinstance(value, bool):
            return "true" if value else "false"

        value = str(value).lower().strip()

        if value not in {
            "true",
            "false",
            "1",
            "0",
        }:
            raise ValueError(
                f"Field '{field.label}' must be boolean."
            )

        return (
            "true"
            if value in {"true", "1"}
            else "false"
        )

    if field_type == "ip":
        try:
            ip_address(value)
        except ValueError:
            raise ValueError(
                f"Field '{field.label}' must contain "
                "a valid IP address."
            )

    if field_type == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError(
                f"Field '{field.label}' must use "
                "YYYY-MM-DD format."
            )

    if field_type == "email":
        if not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            value,
        ):
            raise ValueError(
                f"Field '{field.label}' must contain "
                "a valid email address."
            )

    if field_type == "url":
        if not re.match(
            r"^https?://",
            value,
            re.IGNORECASE,
        ):
            raise ValueError(
                f"Field '{field.label}' must contain "
                "a valid HTTP/HTTPS URL."
            )

    if field_type == "select":
        options = _deserialize_options(
            field.options
        )

        if options and value not in options:
            raise ValueError(
                f"Invalid value for field "
                f"'{field.label}'."
            )

    if field_type == "multiselect":
        if not isinstance(value, list):
            raise ValueError(
                f"Field '{field.label}' must contain "
                "a list of values."
            )

        options = _deserialize_options(
            field.options
        )

        if options:
            invalid = [
                item
                for item in value
                if str(item) not in options
            ]

            if invalid:
                raise ValueError(
                    f"Invalid value for field "
                    f"'{field.label}'."
                )

        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return str(value)


def validate_and_save_custom_fields(
    db: Session,
    asset_type: str,
    asset_id: int,
    values: dict,
):
    fields = list(
        db.scalars(
            select(AssetFieldDefinition).where(
                AssetFieldDefinition.asset_type
                == asset_type
            )
        ).all()
    )

    field_map = {
        field.field_key: field
        for field in fields
    }

    for field in fields:

        if field.system_field:
            continue

        value = values.get(
            field.field_key
        )

        if (
            field.required
            and (
                value is None
                or str(value).strip() == ""
            )
        ):
            raise ValueError(
                f"Required field "
                f"'{field.label}' is missing."
            )

    for key in values:

        if key not in field_map:
            raise ValueError(
                f"Unknown asset field: {key}"
            )

    for key, value in values.items():

        field = field_map[key]

        if field.system_field:
            continue

        normalized = _normalize_value(
            field,
            value,
        )

        existing = db.scalar(
            select(AssetFieldValue).where(
                AssetFieldValue.asset_type
                == asset_type,
                AssetFieldValue.asset_id
                == asset_id,
                AssetFieldValue.field_id
                == field.id,
            )
        )

        if existing:

            existing.value = normalized

        elif normalized is not None:

            db.add(
                AssetFieldValue(
                    asset_type=asset_type,
                    asset_id=asset_id,
                    field_id=field.id,
                    value=normalized,
                )
            )

    db.commit()


def get_asset_field_values(
    db: Session,
    asset_type: str,
    asset_id: int,
):
    definitions = list(
        db.scalars(
            select(AssetFieldDefinition).where(
                AssetFieldDefinition.asset_type
                == asset_type
            )
        ).all()
    )

    values = list(
        db.scalars(
            select(AssetFieldValue).where(
                AssetFieldValue.asset_type
                == asset_type,
                AssetFieldValue.asset_id
                == asset_id,
            )
        ).all()
    )

    value_map = {
        value.field_id: value.value
        for value in values
    }

    result = {}

    for field in definitions:

        if field.system_field:
            continue

        raw_value = value_map.get(
            field.id
        )

        if raw_value is None:
            continue

        if field.field_type == "boolean":
            result[field.field_key] = (
                raw_value == "true"
            )

        elif field.field_type == "number":
            try:
                result[field.field_key] = float(
                    raw_value
                )
            except ValueError:
                result[field.field_key] = raw_value

        elif field.field_type == "multiselect":
            try:
                result[field.field_key] = json.loads(
                    raw_value
                )
            except json.JSONDecodeError:
                result[field.field_key] = []

        else:
            result[field.field_key] = raw_value

    return result