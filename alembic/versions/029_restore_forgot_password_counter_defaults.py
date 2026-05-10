"""Restore DB defaults for forgot-password counters (NOT NULL columns).

Revision ID: 029
Revises: 028
Create Date: 2026-05-07

015 added ``forgot_password_*_attempts`` with server_default then removed it via
``alter_column(..., server_default=None)``, leaving NOT NULL columns with no default.
Inserts that omit those columns (e.g. new owners / employees) then fail with an
integrity/not-null violation.

This migration restores PostgreSQL DEFAULT 0 for those columns.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("companies_owners", "beasy_employees"):
        op.alter_column(
            table,
            "forgot_password_verify_attempts",
            server_default=sa.text("0"),
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        op.alter_column(
            table,
            "forgot_password_resend_attempts",
            server_default=sa.text("0"),
            existing_type=sa.Integer(),
            existing_nullable=False,
        )


def downgrade() -> None:
    for table in ("companies_owners", "beasy_employees"):
        op.alter_column(
            table,
            "forgot_password_verify_attempts",
            server_default=None,
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        op.alter_column(
            table,
            "forgot_password_resend_attempts",
            server_default=None,
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
