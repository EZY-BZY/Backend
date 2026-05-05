"""Drop legacy unused tables from earlier schema versions.

Revision ID: 010
Revises: 009
Create Date: 2026-05-05

This migration removes old tables that are no longer part of the active
application modules and model registry.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Legacy org RBAC table from old employee domain.
    op.execute("DROP TABLE IF EXISTS employee_permissions CASCADE")

    # Legacy marketplace/accounting domain tables (created in 001) that are
    # not used by the active codebase modules.
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")

    op.execute("DROP TABLE IF EXISTS ledger_entries CASCADE")
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TABLE IF EXISTS invoices CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP TABLE IF EXISTS products CASCADE")

    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS companies CASCADE")


def downgrade() -> None:
    # Irreversible cleanup migration: dropped legacy tables are intentionally
    # not recreated here.
    pass
