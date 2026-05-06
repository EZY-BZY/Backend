"""Add French currency fields to countries.

Revision ID: 012
Revises: 011
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "countries",
        sa.Column("currency_shortcut_fr", sa.String(16), nullable=False, server_default=""),
    )
    op.add_column(
        "countries",
        sa.Column("currency_name_fr", sa.String(128), nullable=False, server_default=""),
    )
    # For existing rows, default empty string is acceptable; app-level validation applies on future writes.
    op.alter_column("countries", "currency_shortcut_fr", server_default=None)
    op.alter_column("countries", "currency_name_fr", server_default=None)


def downgrade() -> None:
    op.drop_column("countries", "currency_name_fr")
    op.drop_column("countries", "currency_shortcut_fr")

