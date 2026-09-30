from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
)
from app.services.equipment import (
    create_equipment,
    delete_equipment,
    get_equipment,
    get_equipments,
    update_equipment,
)


router = APIRouter(
    prefix="/api/equipments",
    tags=["Equipment"],
)


@router.get(
    "",
    response_model=list[EquipmentResponse],
)
def list_equipments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_equipments(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{equipment_id}",
    response_model=EquipmentResponse,
)
def read_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
):
    equipment = get_equipment(
        db=db,
        equipment_id=equipment_id,
    )

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.post(
    "",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_equipment_api(
    equipment_data: EquipmentCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_equipment(
            db=db,
            equipment_data=equipment_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.put(
    "/{equipment_id}",
    response_model=EquipmentResponse,
)
def update_equipment_api(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    db: Session = Depends(get_db),
):
    equipment = get_equipment(
        db=db,
        equipment_id=equipment_id,
    )

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    try:
        return update_equipment(
            db=db,
            equipment=equipment,
            equipment_data=equipment_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_equipment_api(
    equipment_id: int,
    db: Session = Depends(get_db),
):
    equipment = get_equipment(
        db=db,
        equipment_id=equipment_id,
    )

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    delete_equipment(
        db=db,
        equipment=equipment,
    )