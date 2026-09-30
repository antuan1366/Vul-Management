from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
)
from app.services.asset_fields import (
    get_asset_field_values,
    validate_and_save_custom_fields,
)


SYSTEM_FIELDS = {
    "name",
    "device_type",
    "vendor",
    "model",
    "version",
    "ip_address",
    "serial_number",
    "cpe",
    "criticality",
    "environment",
    "description",
}


def _validate_system_fields(
    db: Session,
    equipment_data,
):
    from app.models.asset_field import (
        AssetFieldDefinition,
    )

    fields = list(
        db.scalars(
            select(AssetFieldDefinition).where(
                AssetFieldDefinition.asset_type
                == "equipment",
                AssetFieldDefinition.system_field
                == True,
            )
        ).all()
    )

    data = equipment_data.model_dump(
        exclude={"custom_fields"},
    )

    for field in fields:

        if not field.required:
            continue

        value = data.get(
            field.field_key
        )

        if (
            value is None
            or str(value).strip() == ""
        ):
            raise ValueError(
                f"Required field "
                f"'{field.label}' is missing."
            )


def get_equipments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Equipment]:

    statement = (
        select(Equipment)
        .order_by(Equipment.id.desc())
        .offset(skip)
        .limit(limit)
    )

    equipments = list(
        db.scalars(statement).all()
    )

    for equipment in equipments:

        equipment.custom_fields = (
            get_asset_field_values(
                db=db,
                asset_type="equipment",
                asset_id=equipment.id,
            )
        )

    return equipments


def get_equipment(
    db: Session,
    equipment_id: int,
) -> Equipment | None:

    equipment = db.get(
        Equipment,
        equipment_id,
    )

    if equipment is not None:

        equipment.custom_fields = (
            get_asset_field_values(
                db=db,
                asset_type="equipment",
                asset_id=equipment.id,
            )
        )

    return equipment


def create_equipment(
    db: Session,
    equipment_data: EquipmentCreate,
) -> Equipment:

    _validate_system_fields(
        db=db,
        equipment_data=equipment_data,
    )

    data = equipment_data.model_dump(
        exclude={"custom_fields"},
    )

    equipment = Equipment(
        **data
    )

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    validate_and_save_custom_fields(
        db=db,
        asset_type="equipment",
        asset_id=equipment.id,
        values=equipment_data.custom_fields,
    )

    equipment.custom_fields = (
        get_asset_field_values(
            db=db,
            asset_type="equipment",
            asset_id=equipment.id,
        )
    )

    return equipment


def update_equipment(
    db: Session,
    equipment: Equipment,
    equipment_data: EquipmentUpdate,
) -> Equipment:

    _validate_system_fields(
        db=db,
        equipment_data=equipment_data,
    )

    update_data = equipment_data.model_dump(
        exclude_unset=True,
        exclude={"custom_fields"},
    )

    for field, value in update_data.items():
        setattr(
            equipment,
            field,
            value,
        )

    db.commit()
    db.refresh(equipment)

    validate_and_save_custom_fields(
        db=db,
        asset_type="equipment",
        asset_id=equipment.id,
        values=equipment_data.custom_fields,
    )

    equipment.custom_fields = (
        get_asset_field_values(
            db=db,
            asset_type="equipment",
            asset_id=equipment.id,
        )
    )

    return equipment


def delete_equipment(
    db: Session,
    equipment: Equipment,
) -> None:

    db.delete(equipment)
    db.commit()