"""Companies owners table.

Revision ID: 014
Revises: 013
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies_owners",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("phone", sa.String(64), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("last_accepted_terms_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("otp_hash", sa.Text(), nullable=True),
        sa.Column("is_verified_phone", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("join_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "account_status",
            sa.String(32),
            nullable=False,
            server_default="pending_verification",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_companies_owners_phone"),
        sa.ForeignKeyConstraint(["created_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "account_status IN ('active', 'pending_verification', 'suspended', 'blocked', 'deleted')",
            name="ck_companies_owners_account_status",
        ),
    )

    op.create_index("ix_companies_owners_phone", "companies_owners", ["phone"], unique=True)
    op.create_index("ix_companies_owners_email", "companies_owners", ["email"], unique=False)
    op.create_index("ix_companies_owners_name", "companies_owners", ["name"], unique=False)
    op.create_index("ix_companies_owners_account_status", "companies_owners", ["account_status"], unique=False)
    op.create_index("ix_companies_owners_join_date", "companies_owners", ["join_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_companies_owners_join_date", table_name="companies_owners")
    op.drop_index("ix_companies_owners_account_status", table_name="companies_owners")
    op.drop_index("ix_companies_owners_name", table_name="companies_owners")
    op.drop_index("ix_companies_owners_email", table_name="companies_owners")
    op.drop_index("ix_companies_owners_phone", table_name="companies_owners")
    op.drop_table("companies_owners")

