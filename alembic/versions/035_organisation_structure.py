"""organisation_structures table and employee FK.

Revision ID: 035
Revises: 034
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035"
down_revision: Union[str, None] = "034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organisation_structures",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name_en", sa.String(256), nullable=False),
        sa.Column("name_ar", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("department_establish_date", sa.Date(), nullable=True),
        sa.Column("total_salaries", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("total_employees", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organisation_structures_company_id",
        "organisation_structures",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_organisation_structures_is_deleted",
        "organisation_structures",
        ["is_deleted"],
        unique=False,
    )

    op.add_column(
        "company_employees",
        sa.Column("organisation_structure_id", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_foreign_key(
        "fk_company_employees_organisation_structure_id",
        "company_employees",
        "organisation_structures",
        ["organisation_structure_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_company_employees_organisation_structure_id",
        "company_employees",
        ["organisation_structure_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_company_employees_organisation_structure_id", table_name="company_employees")
    op.drop_constraint(
        "fk_company_employees_organisation_structure_id",
        "company_employees",
        type_="foreignkey",
    )
    op.drop_column("company_employees", "organisation_structure_id")
    op.drop_index("ix_organisation_structures_is_deleted", table_name="organisation_structures")
    op.drop_index("ix_organisation_structures_company_id", table_name="organisation_structures")
    op.drop_table("organisation_structures")
