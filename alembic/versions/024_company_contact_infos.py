"""company_contact_infos table.

Revision ID: 024
Revises: 023
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_contact_infos",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("value", sa.String(2048), nullable=False),
        sa.Column("contact_type", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "contact_type IN ("
            "'number', 'facebook', 'instagram', 'tiktok', 'youtube', "
            "'threads', 'whatsapp', 'twitter_x'"
            ")",
            name="ck_company_contact_infos_contact_type",
        ),
    )
    op.create_index(
        "ix_company_contact_infos_company_id",
        "company_contact_infos",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_contact_infos_contact_type",
        "company_contact_infos",
        ["contact_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_company_contact_infos_contact_type", table_name="company_contact_infos")
    op.drop_index("ix_company_contact_infos_company_id", table_name="company_contact_infos")
    op.drop_table("company_contact_infos")
