import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Session

from app.database import Base, get_db


class TablePreference(Base):
    __tablename__ = "table_preferences"

    id = Column(Integer, primary_key=True, index=True)
    table_key = Column(String(80), unique=True, nullable=False, index=True)
    settings_json = Column(Text, nullable=False, default="{}")


router = APIRouter(prefix="/api/table-preferences", tags=["Table Preferences"])
SUPPORTED_TABLES = {"scan-results", "nessus-results", "vulnerabilities"}


class TablePreferenceUpdate(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


@router.get("/{table_key}")
def get_table_preference(table_key: str, db: Session = Depends(get_db)):
    if table_key not in SUPPORTED_TABLES:
        raise HTTPException(status_code=404, detail="Unknown table preference key.")
    record = db.query(TablePreference).filter(TablePreference.table_key == table_key).first()
    if record is None:
        return {"table_key": table_key, "settings": {}}
    try:
        settings = json.loads(record.settings_json or "{}")
    except (TypeError, json.JSONDecodeError):
        settings = {}
    return {"table_key": table_key, "settings": settings}


@router.put("/{table_key}")
def save_table_preference(table_key: str, data: TablePreferenceUpdate, db: Session = Depends(get_db)):
    if table_key not in SUPPORTED_TABLES:
        raise HTTPException(status_code=404, detail="Unknown table preference key.")
    settings = data.settings
    page_size = settings.get("pageSize", 25)
    if not isinstance(page_size, int) or page_size not in {10, 25, 50, 100}:
        raise HTTPException(status_code=400, detail="Rows per page must be 10, 25, 50, or 100.")
    columns = settings.get("columns", {})
    widths = settings.get("widths", {})
    if not isinstance(columns, dict) or not isinstance(widths, dict):
        raise HTTPException(status_code=400, detail="Columns and widths must be objects.")
    for key, visible in columns.items():
        if not isinstance(key, str) or not isinstance(visible, bool):
            raise HTTPException(status_code=400, detail="Column visibility settings are invalid.")
    safe_widths = {}
    for key, width in widths.items():
        if not isinstance(key, str) or not isinstance(width, (int, float)):
            raise HTTPException(status_code=400, detail="Column widths are invalid.")
        safe_widths[key] = max(60, min(900, int(width)))
    normalized = {"pageSize": page_size, "columns": columns, "widths": safe_widths}
    record = db.query(TablePreference).filter(TablePreference.table_key == table_key).first()
    if record is None:
        record = TablePreference(table_key=table_key, settings_json=json.dumps(normalized))
        db.add(record)
    else:
        record.settings_json = json.dumps(normalized)
    db.commit()
    db.refresh(record)
    return {"table_key": table_key, "settings": normalized}
