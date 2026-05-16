"""company_employee_branches — employees assigned to branches.

Revision ID: 032
Revises: 031
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_employee_branches",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_by_type", sa.String(32), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["company_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["company_branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "branch_id", name="uq_company_employee_branches_pair"),
        sa.CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_company_employee_branches_created_by_type",
        ),
    )
    op.create_index(
        "ix_company_employee_branches_employee_id",
        "company_employee_branches",
        ["employee_id"],
    )
    op.create_index(
        "ix_company_employee_branches_branch_id",
        "company_employee_branches",
        ["branch_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_company_employee_branches_branch_id", table_name="company_employee_branches")
    op.drop_index("ix_company_employee_branches_employee_id", table_name="company_employee_branches")
    op.drop_table("company_employee_branches")
