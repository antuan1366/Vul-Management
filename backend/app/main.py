import asyncio
import time as monotonic_time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app.api.application_events import router as application_events_router
from app.api.asset_fields import router as asset_fields_router
from app.api.equipments import router as equipment_router
from app.api.feeds import router as feeds_router
from app.api.health import router as health_router
from app.api.intelligence import router as intelligence_router
from app.api.remediation import router as remediation_router
from app.api.security_identifiers import router as security_identifiers_router
from app.api.sync_jobs import router as sync_jobs_router
from app.api.threat_intelligence import router as threat_intelligence_router
from app.api.telegram_settings import router as telegram_settings_router
from app.api.vulnerability_candidates import router as vulnerability_candidates_router
from app.api.vulnerability_scan import router as vulnerability_scan_router
from app.api.managed_assets import (
    application_router,
    library_router,
    operating_system_router,
)
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
from app.models.application_event import ApplicationEvent
from app.models.application import Application
from app.models.asset_field import AssetFieldDefinition, AssetFieldValue
from app.models.equipment import Equipment
from app.models.feed import Feed
from app.models.library import Library
from app.models.operating_system import OperatingSystem
from app.models.scan_schedule import ScanSchedule
from app.models.security_identifier import SecurityIdentifier
from app.models.security_identifier_check import SecurityIdentifierCheck
from app.models.sync_job import SyncJob
from app.models.threat_intelligence import TelegramFeed, TelegramScanResult, TelegramScanRun, TelegramScanSchedule, ThreatIntelligence
from app.models.vulnerability import AssetVulnerability, Vulnerability
from app.models.vulnerability_candidate import VulnerabilityCandidate
from app.services.asset_fields import seed_default_fields
from app.services.feeds import seed_default_feeds
from app.services.managed_asset_fields import seed_managed_asset_fields
from app.services.scan_scheduler import scheduler_loop
from app.services.application_events import record_event
from app.services.threat_intelligence import telegram_scheduler_loop


existing_tables = set(inspect(engine).get_table_names())
fresh_database = not existing_tables

migrate_equipment_name_nullable()

if fresh_database:
    Base.metadata.create_all(bind=engine)

# Create newly introduced tables on existing installations without altering existing tables.
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = asyncio.create_task(scheduler_loop())
    telegram_scheduler_task = asyncio.create_task(telegram_scheduler_loop())
    try:
        yield
    finally:
        scheduler_task.cancel()
        telegram_scheduler_task.cancel()
        for task in (scheduler_task, telegram_scheduler_task):
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Vulnerability Management Platform",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_api_activity(request: Request, call_next):
    started = monotonic_time.perf_counter()
    path = request.url.path
    method = request.method.upper()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as error:
        if path.startswith("/api/") and not path.startswith("/api/events"):
            record_event(
                "ERROR", "api", "HTTP API", "request_exception",
                f"{method} {path} raised {error.__class__.__name__}: {str(error)[:500]}",
                duration_ms=int((monotonic_time.perf_counter() - started) * 1000),
                details={"method": method, "path": path, "exception_type": error.__class__.__name__},
            )
        raise
    duration_ms = int((monotonic_time.perf_counter() - started) * 1000)
    # Record state-changing requests and all failed API responses. Avoid noisy successful
    # polling/read events and avoid recursive logging of the event viewer itself.
    if path.startswith("/api/") and not path.startswith("/api/events") and (
        method in {"POST", "PUT", "PATCH", "DELETE"} or status >= 400
    ):
        level = "ERROR" if status >= 500 else "WARNING" if status >= 400 else "INFO"
        record_event(
            level, "api", "HTTP API", "request_completed",
            f"{method} {path} returned HTTP {status}.",
            duration_ms=duration_ms,
            details={"method": method, "path": path, "status_code": status},
        )
    return response


app.include_router(health_router)
app.include_router(application_events_router)
app.include_router(equipment_router)
app.include_router(asset_fields_router)
app.include_router(operating_system_router)
app.include_router(application_router)
app.include_router(library_router)
app.include_router(feeds_router)
app.include_router(security_identifiers_router)
app.include_router(intelligence_router)
app.include_router(remediation_router)
app.include_router(sync_jobs_router)
app.include_router(vulnerability_candidates_router)
app.include_router(vulnerability_scan_router)
app.include_router(threat_intelligence_router)
app.include_router(telegram_settings_router)


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
