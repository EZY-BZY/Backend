"""company_employees, company_employee_phones, employees_app_permissions.

Revision ID: 028
Revises: 027
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_employees",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("email", sa.String(512), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("salary", sa.Numeric(14, 2), nullable=True),
        sa.Column("bonus_amount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("salary_system", sa.String(32), nullable=True),
        sa.Column("department", sa.String(256), nullable=True),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_type", sa.String(32), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_type", sa.String(32), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "role IN ('admin', 'employee', 'inventory_manager', 'finance')",
            name="ck_company_employees_role",
        ),
        sa.CheckConstraint(
            "salary_system IS NULL OR salary_system IN ('monthly', 'weekly', 'yearly', 'daily')",
            name="ck_company_employees_salary_system",
        ),
        sa.CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_company_employees_created_by_type",
        ),
        sa.CheckConstraint(
            "updated_by_type IN ('company_owner', 'employee')",
            name="ck_company_employees_updated_by_type",
        ),
        sa.CheckConstraint("salary IS NULL OR salary >= 0", name="ck_company_employees_salary_nonneg"),
        sa.CheckConstraint("bonus_amount >= 0", name="ck_company_employees_bonus_nonneg"),
    )
    op.create_index("ix_company_employees_company_id", "company_employees", ["company_id"], unique=False)
    op.create_index("ix_company_employees_email", "company_employees", ["email"], unique=False)
    op.create_index("ix_company_employees_salary_system", "company_employees", ["salary_system"], unique=False)
    op.create_index("ix_company_employees_department", "company_employees", ["department"], unique=False)
    op.create_index("ix_company_employees_role", "company_employees", ["role"], unique=False)
    op.create_index("ix_company_employees_is_active", "company_employees", ["is_active"], unique=False)

    op.create_table(
        "company_employee_phones",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("phone_number", sa.String(64), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_type", sa.String(32), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_type", sa.String(32), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["company_employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_company_employee_phones_created_by_type",
        ),
        sa.CheckConstraint(
            "updated_by_type IN ('company_owner', 'employee')",
            name="ck_company_employee_phones_updated_by_type",
        ),
    )
    op.create_index(
        "ix_company_employee_phones_employee_id",
        "company_employee_phones",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_employee_phones_phone_number",
        "company_employee_phones",
        ["phone_number"],
        unique=True,
    )
    op.create_index(
        "ix_company_employee_phones_is_active",
        "company_employee_phones",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "uq_company_employee_phones_one_primary_active",
        "company_employee_phones",
        ["employee_id"],
        unique=True,
        postgresql_where=sa.text("is_primary IS TRUE AND is_active IS TRUE"),
    )

    op.create_table(
        "employees_app_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("app_permission_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("assigned_by_type", sa.String(32), nullable=False),
        sa.Column("assigned_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by_type", sa.String(32), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["company_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["app_permission_id"], ["app_permissions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id",
            "app_permission_id",
            name="uq_employees_app_permissions_employee_perm",
        ),
        sa.CheckConstraint(
            "assigned_by_type IN ('company_owner', 'employee')",
            name="ck_employees_app_permissions_assigned_by_type",
        ),
        sa.CheckConstraint(
            "updated_by_type IN ('company_owner', 'employee')",
            name="ck_employees_app_permissions_updated_by_type",
        ),
    )
    op.create_index(
        "ix_employees_app_permissions_employee_id",
        "employees_app_permissions",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_employees_app_permissions_app_permission_id",
        "employees_app_permissions",
        ["app_permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_employees_app_permissions_is_active",
        "employees_app_permissions",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_employees_app_permissions_is_active", table_name="employees_app_permissions")
    op.drop_index("ix_employees_app_permissions_app_permission_id", table_name="employees_app_permissions")
    op.drop_index("ix_employees_app_permissions_employee_id", table_name="employees_app_permissions")
    op.drop_table("employees_app_permissions")

    op.drop_index("uq_company_employee_phones_one_primary_active", table_name="company_employee_phones")
    op.drop_index("ix_company_employee_phones_is_active", table_name="company_employee_phones")
    op.drop_index("ix_company_employee_phones_phone_number", table_name="company_employee_phones")
    op.drop_index("ix_company_employee_phones_employee_id", table_name="company_employee_phones")
    op.drop_table("company_employee_phones")

    op.drop_index("ix_company_employees_is_active", table_name="company_employees")
    op.drop_index("ix_company_employees_role", table_name="company_employees")
    op.drop_index("ix_company_employees_department", table_name="company_employees")
    op.drop_index("ix_company_employees_salary_system", table_name="company_employees")
    op.drop_index("ix_company_employees_email", table_name="company_employees")
    op.drop_index("ix_company_employees_company_id", table_name="company_employees")
    op.drop_table("company_employees")
