from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SecurityIdentifier(Base):
    __tablename__ = "security_identifiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cpe: Mapped[str | None] = mapped_column(Text, nullable=True)
    purl: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unverified"
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
