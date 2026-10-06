"""add asset identification results and history

Revision ID: 0006
Revises: 0005
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("security_identifiers", sa.Column("reason", sa.Text(), nullable=True))
    op.add_column("security_identifiers", sa.Column("candidates", sa.Text(), nullable=True))
    op.add_column("security_identifiers", sa.Column("last_checked_at", sa.DateTime(), nullable=True))

    op.create_table(
        "security_identifier_checks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("cpe", sa.Text(), nullable=True),
        sa.Column("purl", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("candidates", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_security_identifier_checks_asset_type", "security_identifier_checks", ["asset_type"])
    op.create_index("ix_security_identifier_checks_asset_id", "security_identifier_checks", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_security_identifier_checks_asset_id", table_name="security_identifier_checks")
    op.drop_index("ix_security_identifier_checks_asset_type", table_name="security_identifier_checks")
    op.drop_table("security_identifier_checks")
    op.drop_column("security_identifiers", "last_checked_at")
    op.drop_column("security_identifiers", "candidates")
    op.drop_column("security_identifiers", "reason")
