from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.asset_field import (
    AssetFieldDefinitionCreate,
    AssetFieldDefinitionResponse,
    AssetFieldDefinitionUpdate,
)
from app.services.asset_fields import (
    create_asset_field,
    delete_asset_field,
    get_asset_field,
    get_asset_fields,
    update_asset_field,
)


router = APIRouter(
    prefix="/api/asset-fields",
    tags=["Asset Fields"],
)


@router.get(
    "",
    response_model=list[AssetFieldDefinitionResponse],
)
def list_asset_fields(
    asset_type: str = "equipment",
    db: Session = Depends(get_db),
):
    return get_asset_fields(
        db=db,
        asset_type=asset_type,
    )


@router.post(
    "",
    response_model=AssetFieldDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset_field_api(
    field_data: AssetFieldDefinitionCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_asset_field(
            db=db,
            field_data=field_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.put(
    "/{field_id}",
    response_model=AssetFieldDefinitionResponse,
)
def update_asset_field_api(
    field_id: int,
    field_data: AssetFieldDefinitionUpdate,
    db: Session = Depends(get_db),
):
    field = get_asset_field(
        db=db,
        field_id=field_id,
    )

    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset field not found.",
        )

    try:
        return update_asset_field(
            db=db,
            field=field,
            field_data=field_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.delete(
    "/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset_field_api(
    field_id: int,
    db: Session = Depends(get_db),
):
    field = get_asset_field(
        db=db,
        field_id=field_id,
    )

    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset field not found.",
        )

    try:
        delete_asset_field(
            db=db,
            field=field,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )