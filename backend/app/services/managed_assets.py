from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.asset_field import AssetFieldDefinition, AssetFieldValue
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.schemas.managed_asset import ManagedAssetCreate, ManagedAssetUpdate
from app.services.asset_fields import (
    get_asset_field_values,
    validate_and_save_custom_fields,
)


ASSET_CONFIG = {
    "operating_system": {
        "model": OperatingSystem,
        "system_fields": {
            "name", "equipment_id", "vendor", "version", "edition", "build",
            "architecture", "kernel", "cpe", "install_date",
            "support_end_date", "lifecycle_status", "description",
        },
    },
    "application": {
        "model": Application,
        "system_fields": {
            "name", "vendor", "version", "edition", "platform",
            "install_path", "cpe", "owner", "criticality",
            "environment", "description",
        },
    },
    "library": {
        "model": Library,
        "system_fields": {
            "name", "version", "language", "package_manager",
            "package_identifier", "purl", "repository", "vendor",
            "cpe", "description",
        },
    },
}


def get_asset_config(asset_type: str):
    config = ASSET_CONFIG.get(asset_type)

    if config is None:
        raise ValueError(f"Unsupported asset type: {asset_type}.")

    return config


def _validate_system_fields(db: Session, asset_type: str, asset_data):
    fields = list(
        db.scalars(
            select(AssetFieldDefinition).where(
                AssetFieldDefinition.asset_type == asset_type,
                AssetFieldDefinition.system_field == True,
            )
        ).all()
    )

    data = asset_data.model_dump(exclude={"custom_fields"})

    for field in fields:
        if not field.required:
            continue

        value = data.get(field.field_key)

        if value is None or str(value).strip() == "":
            raise ValueError(f"Required field '{field.label}' is missing.")


def _attach_custom_fields(db: Session, asset_type: str, asset):
    asset.custom_fields = get_asset_field_values(
        db=db,
        asset_type=asset_type,
        asset_id=asset.id,
    )
    return asset


def get_assets(db: Session, asset_type: str, skip: int = 0, limit: int = 100):
    config = get_asset_config(asset_type)

    statement = (
        select(config["model"])
        .order_by(config["model"].id.desc())
        .offset(skip)
        .limit(limit)
    )

    assets = list(db.scalars(statement).all())

    return [
        _attach_custom_fields(db, asset_type, asset)
        for asset in assets
    ]


def get_asset(db: Session, asset_type: str, asset_id: int):
    config = get_asset_config(asset_type)
    asset = db.get(config["model"], asset_id)

    if asset is not None:
        _attach_custom_fields(db, asset_type, asset)

    return asset


def create_asset(db: Session, asset_type: str, asset_data: ManagedAssetCreate):
    config = get_asset_config(asset_type)

    _validate_system_fields(db, asset_type, asset_data)

    data = asset_data.model_dump(exclude={"custom_fields"})
    data = {
        key: value
        for key, value in data.items()
        if key in config["system_fields"]
    }

    asset = config["model"](**data)
    db.add(asset)
    db.commit()
    db.refresh(asset)

    validate_and_save_custom_fields(
        db=db,
        asset_type=asset_type,
        asset_id=asset.id,
        values=asset_data.custom_fields,
    )

    return _attach_custom_fields(db, asset_type, asset)


def update_asset(db: Session, asset_type: str, asset, asset_data: ManagedAssetUpdate):
    config = get_asset_config(asset_type)

    _validate_system_fields(db, asset_type, asset_data)

    update_data = asset_data.model_dump(
        exclude_unset=True,
        exclude={"custom_fields"},
    )

    for field, value in update_data.items():
        if field in config["system_fields"]:
            setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    validate_and_save_custom_fields(
        db=db,
        asset_type=asset_type,
        asset_id=asset.id,
        values=asset_data.custom_fields,
    )

    return _attach_custom_fields(db, asset_type, asset)


def delete_asset(db: Session, asset_type: str, asset):
    config = get_asset_config(asset_type)

    db.execute(
        delete(AssetFieldValue).where(
            AssetFieldValue.asset_type == asset_type,
            AssetFieldValue.asset_id == asset.id,
        )
    )

    db.delete(asset)
    db.commit()
