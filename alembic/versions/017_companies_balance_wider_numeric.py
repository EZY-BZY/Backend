"""Widen companies.current_balance for large signed values.

Revision ID: 017
Revises: 016
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "companies",
        "current_balance",
        existing_type=sa.Numeric(18, 2),
        type_=sa.Numeric(38, 8),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "companies",
        "current_balance",
        existing_type=sa.Numeric(38, 8),
        type_=sa.Numeric(18, 2),
        existing_nullable=False,
    )
