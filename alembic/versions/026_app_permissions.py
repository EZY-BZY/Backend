"""app_permissions + app_permissions_history.

Revision ID: 026
Revises: 025
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("permission_tag", sa.String(128), nullable=False),
        sa.Column("permission_label", sa.String(64), nullable=False),
        sa.Column("permission_key", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("permission_key", name="uq_app_permissions_permission_key"),
    )
    op.create_index("ix_app_permissions_permission_tag", "app_permissions", ["permission_tag"], unique=False)
    op.create_index("ix_app_permissions_permission_label", "app_permissions", ["permission_label"], unique=False)
    op.create_index("ix_app_permissions_is_active", "app_permissions", ["is_active"], unique=False)

    op.create_table(
        "app_permissions_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("app_permission_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("permission_key", sa.String(256), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["performed_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action IN ('updated', 'deleted')",
            name="ck_app_permissions_history_action",
        ),
    )
    op.create_index(
        "ix_app_permissions_history_app_permission_id",
        "app_permissions_history",
        ["app_permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_app_permissions_history_permission_key",
        "app_permissions_history",
        ["permission_key"],
        unique=False,
    )
    op.create_index(
        "ix_app_permissions_history_action",
        "app_permissions_history",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_app_permissions_history_performed_at",
        "app_permissions_history",
        ["performed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_app_permissions_history_performed_at", table_name="app_permissions_history")
    op.drop_index("ix_app_permissions_history_action", table_name="app_permissions_history")
    op.drop_index("ix_app_permissions_history_permission_key", table_name="app_permissions_history")
    op.drop_index("ix_app_permissions_history_app_permission_id", table_name="app_permissions_history")
    op.drop_table("app_permissions_history")
    op.drop_index("ix_app_permissions_is_active", table_name="app_permissions")
    op.drop_index("ix_app_permissions_permission_label", table_name="app_permissions")
    op.drop_index("ix_app_permissions_permission_tag", table_name="app_permissions")
    op.drop_table("app_permissions")
