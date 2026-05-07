"""Add is_visible to company_financials_accounts.

Revision ID: 020
Revises: 019
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "company_financials_accounts",
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(
        "ix_company_financials_accounts_is_visible",
        "company_financials_accounts",
        ["is_visible"],
        unique=False,
    )
    op.alter_column("company_financials_accounts", "is_visible", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_company_financials_accounts_is_visible", table_name="company_financials_accounts")
    op.drop_column("company_financials_accounts", "is_visible")
