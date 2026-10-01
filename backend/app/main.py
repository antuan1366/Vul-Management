from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app.api.asset_fields import router as asset_fields_router
from app.api.equipments import router as equipment_router
from app.api.feeds import router as feeds_router
from app.api.health import router as health_router
from app.api.intelligence import router as intelligence_router
from app.api.managed_assets import (
    application_router,
    library_router,
    operating_system_router,
)
from app.api.security_identifiers import router as security_identifiers_router
from app.core.config import settings
from app.core.database_version import (
    ensure_database_version,
    validate_database_compatibility,
)
from app.database import (
    Base,
    SessionLocal,
    engine,
    migrate_equipment_name_nullable,
)

from app.models.application import Application
from app.models.asset_field import AssetFieldDefinition, AssetFieldValue
from app.models.equipment import Equipment
from app.models.feed import Feed
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.models.security_identifier import SecurityIdentifier
from app.models.vulnerability import AssetVulnerability, Vulnerability

from app.services.asset_fields import seed_default_fields
from app.services.feeds import seed_default_feeds
from app.services.managed_asset_fields import seed_managed_asset_fields


existing_tables = set(inspect(engine).get_table_names())
fresh_database = not existing_tables

migrate_equipment_name_nullable()

Base.metadata.create_all(bind=engine)

database_schema_version = ensure_database_version(
    fresh_database=fresh_database,
)
validate_database_compatibility(database_schema_version)


def initialize_database():
    db = SessionLocal()

    try:
        seed_default_fields(db)
        seed_managed_asset_fields(db)
        seed_default_feeds(db)
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


app.include_router(health_router)
app.include_router(equipment_router)
app.include_router(asset_fields_router)
app.include_router(operating_system_router)
app.include_router(application_router)
app.include_router(library_router)
app.include_router(feeds_router)
app.include_router(security_identifiers_router)
app.include_router(intelligence_router)


frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "src"

app.mount(
    "/src",
    StaticFiles(directory=frontend_dir),
    name="frontend",
)


@app.get("/api/info")
def app_info():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "database_schema_version": database_schema_version,
        "database_schema_min": settings.db_schema_min,
        "database_schema_max": settings.db_schema_max,
        "status": "running",
    }


@app.get("/")
def root():
    return RedirectResponse(url="/src/pages/dashboard.html")
