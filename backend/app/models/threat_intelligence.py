from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelegramFeed(Base):
    __tablename__ = "telegram_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel_username: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class TelegramScanRun(Base):
    __tablename__ = "telegram_scan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    channels_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    channels_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    messages_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cve_occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class TelegramScanResult(Base):
    __tablename__ = "telegram_scan_results"
    __table_args__ = (
        UniqueConstraint("channel_username", "telegram_message_id", "cve_id", name="uq_telegram_message_cve"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_run_id: Mapped[int | None] = mapped_column(ForeignKey("telegram_scan_runs.id"), nullable=True, index=True)
    cve_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    channel_name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel_username: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    telegram_message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    message_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    scan_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="new", index=True)
    nvd_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_requested")
    nvd_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    affected_product: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_versions: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    nvd_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    references_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    nvd_missing_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cve_id: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    affected_product: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_versions: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    references_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    nvd_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_channel: Mapped[str | None] = mapped_column(String(150), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    jira_issue_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jira_issue_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    jira_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_sent")
    custom_fields_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class VulnerabilityCustomField(Base):
    __tablename__ = "vulnerability_custom_fields"
    __table_args__ = (
        UniqueConstraint("name", name="uq_vulnerability_custom_fields_name"),
        UniqueConstraint("field_key", name="uq_vulnerability_custom_fields_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_key: Mapped[str] = mapped_column(String(80), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_in_table: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TelegramScanSchedule(Base):
    __tablename__ = "telegram_scan_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    scan_time: Mapped[str] = mapped_column(String(5), nullable=False, default="02:00")
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_run_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
