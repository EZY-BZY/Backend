"""Industries table (multilingual + image path/URL).

Revision ID: 009
Revises: 008
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "industries",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name_en", sa.String(256), nullable=False),
        sa.Column("name_ar", sa.String(256), nullable=False),
        sa.Column("name_fr", sa.String(256), nullable=False),
        sa.Column("image", sa.String(2048), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["beasy_employees.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("industries")
