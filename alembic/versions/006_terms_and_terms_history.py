"""Replace legacy `terms` with new schema; add `terms_history` audit table.

Revision ID: 006
Revises: 005
Create Date: 2026-05-04

Drops the old `terms` table from revision 002 (different columns) and creates
the new multilingual terms model with soft delete and one active row per type.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS terms CASCADE")

    op.create_table(
        "terms",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name_en", sa.String(512), nullable=False),
        sa.Column("name_ar", sa.String(512), nullable=False),
        sa.Column("name_fr", sa.String(512), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("description_ar", sa.Text(), nullable=False),
        sa.Column("description_fr", sa.Text(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "type IN ('privacy_policy', 'terms_of_use', 'refund_terms', 'delivery_terms')",
            name="ck_terms_type",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["beasy_employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_terms_type", "terms", ["type"], unique=False)
    op.create_index("ix_terms_deleted_at", "terms", ["deleted_at"], unique=False)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_terms_one_active_per_type
        ON terms (type)
        WHERE deleted_at IS NULL
        """
    )

    op.create_table(
        "terms_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("term_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("term_type", sa.String(32), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("data_before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("data_after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action IN ('created', 'updated', 'deleted')",
            name="ck_terms_history_action",
        ),
        sa.CheckConstraint(
            "term_type IN ('privacy_policy', 'terms_of_use', 'refund_terms', 'delivery_terms')",
            name="ck_terms_history_term_type",
        ),
        sa.ForeignKeyConstraint(["term_id"], ["terms.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["performed_by"], ["beasy_employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_terms_history_term_id", "terms_history", ["term_id"], unique=False)
    op.create_index("ix_terms_history_term_type", "terms_history", ["term_type"], unique=False)
    op.create_index("ix_terms_history_action", "terms_history", ["action"], unique=False)
    op.create_index("ix_terms_history_performed_at", "terms_history", ["performed_at"], unique=False)


def downgrade() -> None:
    op.drop_table("terms_history")
    op.drop_table("terms")
