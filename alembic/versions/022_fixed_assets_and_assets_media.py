"""Fixed assets and assets_media tables.

Revision ID: 022
Revises: 021
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fixed_assets",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("asset_name", sa.String(512), nullable=False),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("location_description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "asset_type IN ("
            "'cars_and_trucks', 'building_and_real_estate', 'machines', "
            "'computers', 'office_furniture', 'other'"
            ")",
            name="ck_fixed_assets_asset_type",
        ),
    )
    op.create_index("ix_fixed_assets_company_id", "fixed_assets", ["company_id"], unique=False)
    op.create_index("ix_fixed_assets_asset_type", "fixed_assets", ["asset_type"], unique=False)

    op.create_table(
        "assets_media",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("media_type", sa.String(64), nullable=False),
        sa.Column("media_link", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["fixed_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assets_media_asset_id", "assets_media", ["asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assets_media_asset_id", table_name="assets_media")
    op.drop_table("assets_media")
    op.drop_index("ix_fixed_assets_asset_type", table_name="fixed_assets")
    op.drop_index("ix_fixed_assets_company_id", table_name="fixed_assets")
    op.drop_table("fixed_assets")
