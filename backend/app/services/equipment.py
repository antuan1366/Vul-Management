from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate


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

    return list(db.scalars(statement).all())


def get_equipment(
    db: Session,
    equipment_id: int,
) -> Equipment | None:

    return db.get(Equipment, equipment_id)


def create_equipment(
    db: Session,
    equipment_data: EquipmentCreate,
) -> Equipment:

    equipment = Equipment(
        **equipment_data.model_dump()
    )

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    return equipment


def update_equipment(
    db: Session,
    equipment: Equipment,
    equipment_data: EquipmentUpdate,
) -> Equipment:

    update_data = equipment_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)

    return equipment


def delete_equipment(
    db: Session,
    equipment: Equipment,
) -> None:

    db.delete(equipment)
    db.commit()