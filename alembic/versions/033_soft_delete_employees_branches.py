"""Soft-delete flags for company_employees and company_branches.

Revision ID: 033
Revises: 032
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "company_employees",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "company_employees",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_company_employees_is_deleted", "company_employees", ["is_deleted"])

    op.add_column(
        "company_branches",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "company_branches",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_company_branches_is_deleted", "company_branches", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_company_branches_is_deleted", table_name="company_branches")
    op.drop_column("company_branches", "deleted_at")
    op.drop_column("company_branches", "is_deleted")
    op.drop_index("ix_company_employees_is_deleted", table_name="company_employees")
    op.drop_column("company_employees", "deleted_at")
    op.drop_column("company_employees", "is_deleted")
