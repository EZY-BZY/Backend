"""employees.password_hash: VARCHAR(256) -> TEXT (no length cap on stored hashes).

Revision ID: 004
Revises: 003
Create Date: 2026-05-04

Plain passwords are never stored; only derived hashes. TEXT avoids any VARCHAR limit
as algorithms or encodings evolve. Long user passwords are supported in app code via
SHA-256 pre-hash before bcrypt.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "employees",
        "password_hash",
        existing_type=sa.String(length=256),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "employees",
        "password_hash",
        existing_type=sa.Text(),
        type_=sa.String(length=256),
        existing_nullable=False,
    )
