"""Add status to banks_and_wallets.

Revision ID: 019
Revises: 018
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "banks_and_wallets",
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    )
    op.create_index("ix_banks_and_wallets_status", "banks_and_wallets", ["status"], unique=False)
    op.create_check_constraint(
        "ck_banks_and_wallets_status",
        "banks_and_wallets",
        "status IN ('active', 'inactive')",
    )
    op.alter_column("banks_and_wallets", "status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_banks_and_wallets_status", "banks_and_wallets", type_="check")
    op.drop_index("ix_banks_and_wallets_status", table_name="banks_and_wallets")
    op.drop_column("banks_and_wallets", "status")
