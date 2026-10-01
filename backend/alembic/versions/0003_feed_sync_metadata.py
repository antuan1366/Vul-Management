"""add synchronization metadata

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("feeds", sa.Column("last_sync_at", sa.DateTime(), nullable=True))
    op.add_column("feeds", sa.Column("last_sync_status", sa.String(length=30), nullable=True))
    op.add_column("feeds", sa.Column("last_sync_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("feeds", "last_sync_message")
    op.drop_column("feeds", "last_sync_status")
    op.drop_column("feeds", "last_sync_at")
