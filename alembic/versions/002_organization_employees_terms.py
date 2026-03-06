"""Organization module: employees, employee_permissions, terms.

Revision ID: 002
Revises: 001
Create Date: 2025-03-06 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Employees: one owner per system enforced by partial unique index
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("account_status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "account_type IN ('owner', 'admin', 'member')",
            name="ck_employees_account_type",
        ),
        sa.CheckConstraint(
            "account_status IN ('active', 'inactive', 'suspended')",
            name="ck_employees_account_status",
        ),
    )
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.create_index("ix_employees_account_type", "employees", ["account_type"], unique=False)
    op.create_index("ix_employees_account_status", "employees", ["account_status"], unique=False)
    # Only one owner in the whole system
    # Only one owner in the system (partial unique index)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_employees_one_owner ON employees (account_type)
        WHERE account_type = 'owner' AND deleted_at IS NULL
        """
    )
    op.create_foreign_key(
        "fk_employees_created_by",
        "employees",
        "employees",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_employees_updated_by",
        "employees",
        "employees",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Employee permissions (permission names checked at runtime)
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
    op.create_index("ix_employee_permissions_employee_id", "employee_permissions", ["employee_id"], unique=False)
    op.create_index("ix_employee_permissions_permission_name", "employee_permissions", ["permission_name"], unique=False)

    # Terms and conditions (multilingual)
    op.create_table(
        "terms",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("term_title_ar", sa.String(512), nullable=True),
        sa.Column("term_title_en", sa.String(512), nullable=True),
        sa.Column("term_title_fr", sa.String(512), nullable=True),
        sa.Column("term_desc_ar", sa.Text(), nullable=True),
        sa.Column("term_desc_en", sa.Text(), nullable=True),
        sa.Column("term_desc_fr", sa.Text(), nullable=True),
        sa.Column("term_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("term_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="valid"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "term_type IN ('privacy_policy', 'terms_of_use', 'cookies_terms')",
            name="ck_terms_term_type",
        ),
        sa.CheckConstraint(
            "status IN ('valid', 'invalid')",
            name="ck_terms_status",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_terms_term_type", "terms", ["term_type"], unique=False)
    op.create_index("ix_terms_status", "terms", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("terms")
    op.drop_table("employee_permissions")
    op.drop_table("employees")
