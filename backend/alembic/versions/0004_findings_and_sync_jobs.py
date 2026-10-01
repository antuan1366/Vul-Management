"""reset intelligence data and add approval workflow/sync jobs

Revision ID: 0004
Revises: 0003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Development reset requested for the current test database.
    # Assets and configuration are intentionally cleared as well so the next
    # run starts from a clean state; default fields/feeds are re-seeded by app startup.
    for table in (
        "asset_vulnerabilities",
        "vulnerabilities",
        "security_identifiers",
        "vulnerability_candidates",
        "sync_jobs",
        "operating_systems",
        "applications",
        "libraries",
        "equipment",
        "asset_field_values",
        "asset_field_definitions",
        "feeds",
    ):
        bind.execute(sa.text(f"DELETE FROM {table}"))

    op.create_table(
        "vulnerability_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cve_id", sa.String(length=30), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("affected_product", sa.Text(), nullable=True),
        sa.Column("affected_versions", sa.Text(), nullable=True),
        sa.Column("references", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("modified_at", sa.DateTime(), nullable=True),
        sa.Column("match_status", sa.String(length=30), nullable=False),
        sa.Column("match_method", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("processed", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(length=255), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sync_jobs")
    op.drop_table("vulnerability_candidates")
