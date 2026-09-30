from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.asset_fields import router as asset_fields_router
from app.api.equipments import router as equipment_router
from app.api.health import router as health_router
from app.api.managed_assets import (
    application_router,
    library_router,
    operating_system_router,
)
from app.core.config import settings
from app.database import (
    Base,
    SessionLocal,
    engine,
    migrate_equipment_name_nullable,
)

from app.models.asset_field import (
    AssetFieldDefinition,
    AssetFieldValue,
)
from app.models.application import Application
from app.models.equipment import Equipment
from app.models.library import Library
from app.models.operating_system import OperatingSystem

from app.services.asset_fields import (
    seed_default_fields,
)
from app.services.managed_asset_fields import (
    seed_managed_asset_fields,
)


migrate_equipment_name_nullable()

Base.metadata.create_all(bind=engine)


def initialize_database():
    db = SessionLocal()

    try:
        seed_default_fields(db)
    seed_managed_asset_fields(db)

    finally:
        db.close()


initialize_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Vulnerability Management Platform",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router
)

app.include_router(
    equipment_router
)

app.include_router(
    asset_fields_router
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }