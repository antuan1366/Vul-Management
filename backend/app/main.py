import asyncio,time as monotonic_time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from urllib.parse import quote
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
from app.api.auth import active_session_user_id, router as auth_router, users_exist
from app.api.users import router as users_router
from app.api.application_events import router as application_events_router
from app.api.asset_fields import router as asset_fields_router
from app.api.equipments import router as equipment_router
from app.api.feeds import router as feeds_router
from app.api.health import router as health_router
from app.api.intelligence import router as intelligence_router
from app.api.nessus import router as nessus_router
from app.api.remediation import router as remediation_router
from app.api.security_identifiers import router as security_identifiers_router
from app.api.sync_jobs import router as sync_jobs_router
from app.api.threat_intelligence import router as threat_intelligence_router
from app.api.telegram_settings import router as telegram_settings_router
from app.api.table_preferences import router as table_preferences_router
from app.api.vulnerability_candidates import router as vulnerability_candidates_router
from app.api.vulnerability_scan import router as vulnerability_scan_router
from app.api.managed_assets import application_router,library_router,operating_system_router
from app.core.config import settings
from app.core.database_version import ensure_database_version,validate_database_compatibility
from app.database import Base,SessionLocal,engine,migrate_equipment_name_nullable
from app.models.application_event import ApplicationEvent
from app.models.application import Application
from app.models.asset_field import AssetFieldDefinition,AssetFieldValue
from app.models.equipment import Equipment
from app.models.feed import Feed
from app.models.library import Library
from app.models.nessus import NessusFinding,NessusHostMapping,NessusImport
from app.models.operating_system import OperatingSystem
from app.models.scan_schedule import ScanSchedule
from app.models.security_identifier import SecurityIdentifier
from app.models.security_identifier_check import SecurityIdentifierCheck
from app.models.sync_job import SyncJob
from app.models.threat_intelligence import TelegramFeed,TelegramScanResult,TelegramScanRun,TelegramScanSchedule,ThreatIntelligence
from app.models.vulnerability import AssetVulnerability,Vulnerability
from app.models.vulnerability_candidate import VulnerabilityCandidate
from app.models.user import User
from app.services.asset_fields import seed_default_fields
from app.services.feeds import seed_default_feeds
from app.services.managed_asset_fields import seed_managed_asset_fields
from app.services.scan_scheduler import scheduler_loop
from app.services.application_events import record_event
from app.services.threat_intelligence import telegram_scheduler_loop

existing=set(inspect(engine).get_table_names())
fresh=not existing
migrate_equipment_name_nullable()
# Fresh installs need their baseline tables before Alembic stamps the head.
# Existing installs must migrate before create_all, otherwise create_all would
# pre-create 0008 tables and cause the migration to fail with "already exists".
if fresh:
    Base.metadata.create_all(bind=engine)
database_schema_version=ensure_database_version(fresh_database=fresh)
Base.metadata.create_all(bind=engine)
validate_database_compatibility(database_schema_version)

def initialize_database():
    db=SessionLocal()
    try:
        seed_default_fields(db);seed_managed_asset_fields(db);seed_default_feeds(db)
    finally:db.close()
initialize_database()

@asynccontextmanager
async def lifespan(app:FastAPI):
    tasks=[asyncio.create_task(scheduler_loop()),asyncio.create_task(telegram_scheduler_loop())]
    try:yield
    finally:
        for task in tasks:task.cancel()
        for task in tasks:
            try:await task
            except asyncio.CancelledError:pass
app=FastAPI(title=settings.app_name,version=settings.app_version,description="Vulnerability Management Platform",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.middleware("http")
async def log_api_activity(request:Request,call_next):
    started=monotonic_time.perf_counter();path=request.url.path;method=request.method.upper()
    try:response=await call_next(request);status=response.status_code
    except Exception as error:
        if path.startswith("/api/") and not path.startswith("/api/events"):record_event("ERROR","api","HTTP API","request_exception",f"{method} {path} raised {error.__class__.__name__}: {str(error)[:500]}",duration_ms=int((monotonic_time.perf_counter()-started)*1000),details={"method":method,"path":path,"exception_type":error.__class__.__name__})
        raise
    duration=int((monotonic_time.perf_counter()-started)*1000)
    if path.startswith("/api/") and not path.startswith("/api/events") and (method in {"POST","PUT","PATCH","DELETE"} or status>=400):
        level="ERROR" if status>=500 else "WARNING" if status>=400 else "INFO"
        record_event(level,"api","HTTP API","request_completed",f"{method} {path} returned HTTP {status}.",duration_ms=duration,details={"method":method,"path":path,"status_code":status})
    return response


@app.middleware("http")
async def enforce_authentication(request: Request, call_next):
    path = request.url.path

    if request.method == "OPTIONS":
        return await call_next(request)

    public_api_paths = {
        "/api/health",
        "/api/auth/status",
        "/api/auth/login",
        "/api/auth/setup",
        "/api/auth/logout",
    }
    if path in public_api_paths:
        return await call_next(request)

    # These files only contain presentation and client-side API wrappers.
    # Every data API and every page HTML document is protected below.
    if path.startswith("/src/styles/") or path.startswith("/src/services/"):
        return await call_next(request)

    signed_in_user_id = active_session_user_id(request)
    has_users = users_exist()

    if path == "/":
        if not has_users:
            return RedirectResponse("/src/pages/setup.html", status_code=303)
        if signed_in_user_id is not None:
            return RedirectResponse("/src/pages/dashboard.html", status_code=303)
        return RedirectResponse("/src/pages/login.html", status_code=303)

    if path == "/src/pages/login.html":
        if not has_users:
            return RedirectResponse("/src/pages/setup.html", status_code=303)
        if signed_in_user_id is not None:
            return RedirectResponse("/src/pages/dashboard.html", status_code=303)
        return await call_next(request)

    if path == "/src/pages/setup.html":
        if has_users:
            destination = (
                "/src/pages/dashboard.html"
                if signed_in_user_id is not None
                else "/src/pages/login.html"
            )
            return RedirectResponse(destination, status_code=303)
        return await call_next(request)

    if path == "/src/pages/users.html" and signed_in_user_id is not None:
        with SessionLocal() as auth_db:
            signed_in_user = auth_db.get(User, signed_in_user_id)
            if signed_in_user is None or signed_in_user.role != "admin":
                return RedirectResponse("/src/pages/dashboard.html", status_code=303)

    protected_api = path.startswith("/api/")
    protected_page = path.startswith("/src/pages/") and path.endswith(".html")
    protected_docs = path in {"/docs", "/redoc", "/openapi.json"}

    if (protected_api or protected_page or protected_docs) and path not in public_api_paths:
        if not has_users:
            if protected_api:
                return JSONResponse(
                    {"detail": "Initial administrator setup is required."},
                    status_code=401,
                )
            return RedirectResponse("/src/pages/setup.html", status_code=303)

        if signed_in_user_id is None:
            if protected_api:
                return JSONResponse(
                    {"detail": "Authentication required. Please sign in."},
                    status_code=401,
                )
            next_target = path
            if request.url.query:
                next_target += "?" + request.url.query
            login_url = "/src/pages/login.html?next=" + quote(next_target, safe="")
            return RedirectResponse(login_url, status_code=303)

    return await call_next(request)

for router in (auth_router,users_router,health_router,application_events_router,equipment_router,asset_fields_router,operating_system_router,application_router,library_router,feeds_router,security_identifiers_router,intelligence_router,remediation_router,sync_jobs_router,vulnerability_candidates_router,vulnerability_scan_router,threat_intelligence_router,telegram_settings_router,table_preferences_router,nessus_router):app.include_router(router)
frontend_dir=Path(__file__).resolve().parents[2]/"frontend"/"src"
app.mount("/src",StaticFiles(directory=frontend_dir),name="frontend")
@app.get("/api/info")
def app_info():return {"name":settings.app_name,"version":settings.app_version,"database_schema_version":database_schema_version,"database_schema_min":settings.db_schema_min,"database_schema_max":settings.db_schema_max,"status":"running"}
@app.get("/")
def root():return RedirectResponse(url="/src/pages/dashboard.html")
