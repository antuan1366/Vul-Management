from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.managed_asset import (
    ManagedAssetCreate,
    ManagedAssetResponse,
    ManagedAssetUpdate,
)
from app.services.managed_assets import (
    get_asset,
    get_asset_config,
    get_assets,
    create_asset,
    delete_asset,
    update_asset,
)


def build_router(asset_type: str, title: str, path_name: str) -> APIRouter:
    router = APIRouter(
        prefix=f"/api/{path_name}",
        tags=[title],
    )

    @router.get("", response_model=list[ManagedAssetResponse])
    def list_assets(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
    ):
        return get_assets(db=db, asset_type=asset_type, skip=skip, limit=limit)

    @router.get("/{asset_id}", response_model=ManagedAssetResponse)
    def read_asset(
        asset_id: int,
        db: Session = Depends(get_db),
    ):
        asset = get_asset(db=db, asset_type=asset_type, asset_id=asset_id)

        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{title} not found.",
            )

        return asset

    @router.post(
        "",
        response_model=ManagedAssetResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_asset_api(
        asset_data: ManagedAssetCreate,
        db: Session = Depends(get_db),
    ):
        try:
            return create_asset(
                db=db,
                asset_type=asset_type,
                asset_data=asset_data,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            )

    @router.put("/{asset_id}", response_model=ManagedAssetResponse)
    def update_asset_api(
        asset_id: int,
        asset_data: ManagedAssetUpdate,
        db: Session = Depends(get_db),
    ):
        asset = get_asset(
            db=db,
            asset_type=asset_type,
            asset_id=asset_id,
        )

        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{title} not found.",
            )

        try:
            return update_asset(
                db=db,
                asset_type=asset_type,
                asset=asset,
                asset_data=asset_data,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            )

    @router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_asset_api(
        asset_id: int,
        db: Session = Depends(get_db),
    ):
        asset = get_asset(
            db=db,
            asset_type=asset_type,
            asset_id=asset_id,
        )

        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{title} not found.",
            )

        delete_asset(
            db=db,
            asset_type=asset_type,
            asset=asset,
        )

    return router


operating_system_router = build_router("operating_system", "Operating Systems", "operating-systems")
application_router = build_router("application", "Applications", "applications")
library_router = build_router("library", "Libraries", "libraries")
