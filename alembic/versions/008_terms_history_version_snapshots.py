"""Replace terms_history with per-type list snapshots per change.

Revision ID: 008
Revises: 007
Create Date: 2026-05-04

Each row stores one version: full ordered list of terms for that type after the
change, plus action, actor, changed term id, and version timestamp.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("terms_history")
    op.create_table(
        "terms_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("term_type", sa.String(32), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("version_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("changed_term_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("terms_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action IN ('created', 'updated', 'deleted')",
            name="ck_terms_history_action",
        ),
        sa.CheckConstraint(
            "term_type IN ('privacy_policy', 'terms_of_use', 'refund_terms', 'delivery_terms')",
            name="ck_terms_history_term_type",
        ),
        sa.ForeignKeyConstraint(["performed_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["changed_term_id"], ["terms.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_terms_history_term_type", "terms_history", ["term_type"], unique=False)
    op.create_index("ix_terms_history_version_at", "terms_history", ["version_at"], unique=False)


def downgrade() -> None:
    op.drop_table("terms_history")
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
