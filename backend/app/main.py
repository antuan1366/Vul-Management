from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.equipments import router as equipment_router
from app.api.health import router as health_router
from app.core.config import settings
from app.database import Base, engine

from app.models.equipment import Equipment


Base.metadata.create_all(bind=engine)


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


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }