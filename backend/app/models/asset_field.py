from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssetFieldDefinition(Base):
    __tablename__ = "asset_field_definitions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    field_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    field_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    system_field: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    editable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    deletable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    options: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AssetFieldValue(Base):
    __tablename__ = "asset_field_values"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    asset_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    field_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )