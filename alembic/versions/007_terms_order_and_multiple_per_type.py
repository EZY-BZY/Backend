"""Allow multiple terms per type; add display order column.

Revision ID: 007
Revises: 006
Create Date: 2026-05-04

Removes the partial unique index (one active row per type). Adds integer column
`order` (quoted in PostgreSQL) for sort order within a type.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_terms_one_active_per_type")
    op.add_column(
        "terms",
        sa.Column("order", sa.Integer(), nullable=False, server_default="1"),
    )
    op.execute('UPDATE terms SET "order" = 1')
    op.create_index("ix_terms_type_order", "terms", ["type", "order"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_terms_type_order", table_name="terms")
    op.drop_column("terms", "order")
    op.execute(
        """
        CREATE UNIQUE INDEX uq_terms_one_active_per_type
        ON terms (type)
        WHERE deleted_at IS NULL
        """
    )
