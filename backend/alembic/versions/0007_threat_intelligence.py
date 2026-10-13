"""add Telegram threat intelligence tables

Revision ID: 0007
Revises: 0006
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_scan_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="daily"),
        sa.Column("scan_time", sa.String(length=5), nullable=False, server_default="02:00"),
        sa.Column("day_of_week", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_run_date", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_telegram_scan_schedules_id", "telegram_scan_schedules", ["id"])

    op.create_table(
        "telegram_feeds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("channel_username", sa.String(length=150), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_message_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("channel_username", name="uq_telegram_feeds_channel_username"),
    )
    op.create_index("ix_telegram_feeds_id", "telegram_feeds", ["id"])
    op.create_index("ix_telegram_feeds_channel_username", "telegram_feeds", ["channel_username"])

    op.create_table(
        "telegram_scan_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("channels_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("channels_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cve_occurrences", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_telegram_scan_runs_id", "telegram_scan_runs", ["id"])
    op.create_index("ix_telegram_scan_runs_status", "telegram_scan_runs", ["status"])

    op.create_table(
        "telegram_scan_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_run_id", sa.Integer(), sa.ForeignKey("telegram_scan_runs.id"), nullable=True),
        sa.Column("cve_id", sa.String(length=30), nullable=False),
        sa.Column("channel_name", sa.String(length=150), nullable=False),
        sa.Column("channel_username", sa.String(length=150), nullable=False),
        sa.Column("telegram_message_id", sa.Integer(), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("message_url", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("scan_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("review_status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("nvd_status", sa.String(length=30), nullable=False, server_default="not_requested"),
        sa.Column("nvd_error", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("affected_product", sa.Text(), nullable=True),
        sa.Column("affected_versions", sa.Text(), nullable=True),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("mitigation", sa.Text(), nullable=True),
        sa.Column("nvd_description", sa.Text(), nullable=True),
        sa.Column("references_text", sa.Text(), nullable=True),
        sa.Column("nvd_missing_fields", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("channel_username", "telegram_message_id", "cve_id", name="uq_telegram_message_cve"),
    )
    for column in ("id", "cve_id", "channel_username", "date", "review_status", "scan_run_id"):
        op.create_index(f"ix_telegram_scan_results_{column}", "telegram_scan_results", [column])

    op.create_table(
        "threat_intelligence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cve_id", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("affected_product", sa.Text(), nullable=True),
        sa.Column("affected_versions", sa.Text(), nullable=True),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("mitigation", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("references_text", sa.Text(), nullable=True),
        sa.Column("nvd_url", sa.Text(), nullable=True),
        sa.Column("source_message", sa.Text(), nullable=True),
        sa.Column("source_channel", sa.String(length=150), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("jira_issue_key", sa.String(length=100), nullable=True),
        sa.Column("jira_issue_url", sa.Text(), nullable=True),
        sa.Column("jira_status", sa.String(length=30), nullable=False, server_default="not_sent"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("cve_id", name="uq_threat_intelligence_cve_id"),
    )
    op.create_index("ix_threat_intelligence_id", "threat_intelligence", ["id"])
    op.create_index("ix_threat_intelligence_cve_id", "threat_intelligence", ["cve_id"])
    op.create_index("ix_threat_intelligence_date", "threat_intelligence", ["date"])


def downgrade() -> None:
    op.drop_table("telegram_scan_schedules")
    op.drop_table("threat_intelligence")
    op.drop_table("telegram_scan_results")
    op.drop_table("telegram_scan_runs")
    op.drop_table("telegram_feeds")
