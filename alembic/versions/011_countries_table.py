"""Countries table (phone/currency/icon + multilingual).

Revision ID: 011
Revises: 010
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("phone_code", sa.String(16), nullable=False),
        sa.Column("name_en", sa.String(256), nullable=False),
        sa.Column("name_ar", sa.String(256), nullable=False),
        sa.Column("name_fr", sa.String(256), nullable=False),
        sa.Column("phone_regex", sa.String(512), nullable=False),
        sa.Column("currency_shortcut_en", sa.String(16), nullable=False),
        sa.Column("currency_shortcut_ar", sa.String(16), nullable=False),
        sa.Column("currency_name_en", sa.String(128), nullable=False),
        sa.Column("currency_name_ar", sa.String(128), nullable=False),
        sa.Column("icon", sa.String(2048), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_code", name="uq_countries_phone_code"),
        sa.UniqueConstraint("name_en", name="uq_countries_name_en"),
        sa.ForeignKeyConstraint(["created_by"], ["beasy_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["beasy_employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_countries_phone_code", "countries", ["phone_code"], unique=True)
    op.create_index("ix_countries_name_en", "countries", ["name_en"], unique=True)


def downgrade() -> None:
    op.drop_table("countries")

