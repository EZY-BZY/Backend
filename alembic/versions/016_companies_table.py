"""Companies table.

Revision ID: 016
Revises: 015
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_name_ar", sa.String(256), nullable=False),
        sa.Column("company_name_en", sa.String(256), nullable=True),
        sa.Column("company_description_ar", sa.Text(), nullable=False),
        sa.Column("company_description_en", sa.Text(), nullable=True),
        sa.Column("show_branches", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("show_products", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("show_social_media", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("show_contact_info", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("image", sa.String(2048), nullable=True),
        sa.Column("service", sa.String(32), nullable=False),
        sa.Column("current_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_number", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["companies_owners.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_companies_status"),
        sa.CheckConstraint(
            "service IN ('services', 'products', 'products_and_services')",
            name="ck_companies_service",
        ),
    )
    op.create_index("ix_companies_owner_id", "companies", ["owner_id"], unique=False)
    op.create_index("ix_companies_status", "companies", ["status"], unique=False)
    op.create_index("ix_companies_service", "companies", ["service"], unique=False)

    op.alter_column("companies", "show_branches", server_default=None)
    op.alter_column("companies", "show_products", server_default=None)
    op.alter_column("companies", "show_social_media", server_default=None)
    op.alter_column("companies", "show_contact_info", server_default=None)
    op.alter_column("companies", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_companies_service", table_name="companies")
    op.drop_index("ix_companies_status", table_name="companies")
    op.drop_index("ix_companies_owner_id", table_name="companies")
    op.drop_table("companies")
