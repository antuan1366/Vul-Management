from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OperatingSystem(Base):
    __tablename__ = "operating_systems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    equipment_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    edition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    build: Mapped[str | None] = mapped_column(String(255), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kernel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cpe: Mapped[str | None] = mapped_column(String(500), nullable=True)
    install_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    support_end_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lifecycle_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
