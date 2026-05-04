"""Rename employees table to beasy_employees (Beasy employees domain).

Revision ID: 005
Revises: 004
Create Date: 2026-05-04

PostgreSQL updates foreign keys from other tables (e.g. terms) when the referenced
table is renamed. Self-referential FKs on this table move with it.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("employees", "beasy_employees")


def downgrade() -> None:
    op.rename_table("beasy_employees", "employees")
