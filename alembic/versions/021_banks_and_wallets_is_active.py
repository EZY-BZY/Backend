"""Replace banks_and_wallets status string with is_active boolean.

Revision ID: 021
Revises: 020
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "banks_and_wallets",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.execute(sa.text("UPDATE banks_and_wallets SET is_active = (status = 'active')"))
    op.drop_constraint("ck_banks_and_wallets_status", "banks_and_wallets", type_="check")
    op.drop_index("ix_banks_and_wallets_status", table_name="banks_and_wallets")
    op.drop_column("banks_and_wallets", "status")
    op.create_index("ix_banks_and_wallets_is_active", "banks_and_wallets", ["is_active"], unique=False)
    op.alter_column("banks_and_wallets", "is_active", server_default=None)


def downgrade() -> None:
    op.add_column(
        "banks_and_wallets",
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    )
    op.execute(
        sa.text(
            "UPDATE banks_and_wallets SET status = CASE WHEN is_active THEN 'active' ELSE 'inactive' END"
        )
    )
    op.drop_index("ix_banks_and_wallets_is_active", table_name="banks_and_wallets")
    op.drop_column("banks_and_wallets", "is_active")
    op.create_index("ix_banks_and_wallets_status", "banks_and_wallets", ["status"], unique=False)
    op.create_check_constraint(
        "ck_banks_and_wallets_status",
        "banks_and_wallets",
        "status IN ('active', 'inactive')",
    )
    op.alter_column("banks_and_wallets", "status", server_default=None)
