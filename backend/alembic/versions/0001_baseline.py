"""baseline current Vul-Management schema

Revision ID: 0001
Revises:
Create Date: 2026-10-01
"""

from typing import Sequence, Union

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing databases are stamped with this baseline after SQLAlchemy
    # creates the current schema. Future schema changes must use migrations.
    pass


def downgrade() -> None:
    # Baseline downgrade is intentionally empty.
    pass
