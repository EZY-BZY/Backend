"""Beasy employees: align employees schema with app (super_user, name, no permissions table).

Revision ID: 003
Revises: 002
Create Date: 2026-05-04

Changes:
- Drop employee_permissions (no longer used by the app).
- Rename employees.full_name -> employees.name.
- Migrate account_type 'owner' -> 'super_user' for existing rows.
- Replace account_type check constraint (owner,admin,member) -> (super_user,admin,member).
- Replace partial unique index one-owner -> one-super_user.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("employee_permissions")

    op.execute("DROP INDEX IF EXISTS uq_employees_one_owner")
    op.drop_constraint("ck_employees_account_type", "employees", type_="check")

    op.execute(
        "UPDATE employees SET account_type = 'super_user' WHERE account_type = 'owner'"
    )

    op.create_check_constraint(
        "ck_employees_account_type",
        "employees",
        "account_type IN ('super_user', 'admin', 'member')",
    )

    op.alter_column(
        "employees",
        "full_name",
        new_column_name="name",
        existing_type=sa.String(length=256),
        existing_nullable=False,
    )

    op.execute(
        """
        CREATE UNIQUE INDEX uq_employees_one_super_user ON employees (account_type)
        WHERE account_type = 'super_user' AND deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_employees_one_super_user")

    op.alter_column(
        "employees",
        "name",
        new_column_name="full_name",
        existing_type=sa.String(length=256),
        existing_nullable=False,
    )

    op.drop_constraint("ck_employees_account_type", "employees", type_="check")

    op.execute(
        "UPDATE employees SET account_type = 'owner' WHERE account_type = 'super_user'"
    )

    op.create_check_constraint(
        "ck_employees_account_type",
        "employees",
        "account_type IN ('owner', 'admin', 'member')",
    )

    op.execute(
        """
        CREATE UNIQUE INDEX uq_employees_one_owner ON employees (account_type)
        WHERE account_type = 'owner' AND deleted_at IS NULL
        """
    )

    op.create_table(
        "employee_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("permission_name", sa.String(128), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "permission_name", name="uq_employee_permissions"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["employees.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_employee_permissions_employee_id",
        "employee_permissions",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_employee_permissions_permission_name",
        "employee_permissions",
        ["permission_name"],
        unique=False,
    )
