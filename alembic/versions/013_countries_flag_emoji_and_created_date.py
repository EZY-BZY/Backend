"""Countries: change icon to flag emoji + add created_date.

Revision ID: 013
Revises: 012
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # icon column now stores flag emoji text; shrink column type.
    op.alter_column(
        "countries",
        "icon",
        existing_type=sa.String(length=2048),
        type_=sa.String(length=16),
        existing_nullable=False,
    )

    op.add_column(
        "countries",
        sa.Column("created_date", sa.Date(), nullable=False, server_default=sa.func.current_date()),
    )
    op.alter_column("countries", "created_date", server_default=None)


def downgrade() -> None:
    op.drop_column("countries", "created_date")
    op.alter_column(
        "countries",
        "icon",
        existing_type=sa.String(length=16),
        type_=sa.String(length=2048),
        existing_nullable=False,
    )

