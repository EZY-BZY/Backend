"""Banks / wallets catalog + company financial accounts.

Revision ID: 018
Revises: 017
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "banks_and_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name_ar", sa.String(256), nullable=False),
        sa.Column("name_en", sa.String(256), nullable=False),
        sa.Column("image", sa.String(2048), nullable=False),
        sa.Column("country_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "type IN ('bank', 'wallet', 'app')",
            name="ck_banks_and_wallets_type",
        ),
    )
    op.create_index("ix_banks_and_wallets_country_id", "banks_and_wallets", ["country_id"], unique=False)
    op.create_index("ix_banks_and_wallets_type", "banks_and_wallets", ["type"], unique=False)

    op.create_table(
        "company_financials_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("banks_and_wallets_type_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("account_number", sa.String(256), nullable=False),
        sa.Column("account_name", sa.String(256), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["banks_and_wallets_type_id"],
            ["banks_and_wallets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["companies_owners.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_company_financials_accounts_company_id",
        "company_financials_accounts",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_financials_accounts_banks_and_wallets_type_id",
        "company_financials_accounts",
        ["banks_and_wallets_type_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_financials_accounts_created_by",
        "company_financials_accounts",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_company_financials_accounts_created_by",
        table_name="company_financials_accounts",
    )
    op.drop_index(
        "ix_company_financials_accounts_banks_and_wallets_type_id",
        table_name="company_financials_accounts",
    )
    op.drop_index(
        "ix_company_financials_accounts_company_id",
        table_name="company_financials_accounts",
    )
    op.drop_table("company_financials_accounts")
    op.drop_index("ix_banks_and_wallets_type", table_name="banks_and_wallets")
    op.drop_index("ix_banks_and_wallets_country_id", table_name="banks_and_wallets")
    op.drop_table("banks_and_wallets")
