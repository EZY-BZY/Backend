"""Restore DEFAULT on countries.created_date.

Revision ID: 030
Revises: 029
Create Date: 2026-05-11

013 added ``created_date`` NOT NULL then removed server_default, so inserts that
omit the column fail. Restore PostgreSQL DEFAULT CURRENT_DATE.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "countries",
        "created_date",
        server_default=sa.text("CURRENT_DATE"),
        existing_type=sa.Date(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "countries",
        "created_date",
        server_default=None,
        existing_type=sa.Date(),
        existing_nullable=False,
    )
