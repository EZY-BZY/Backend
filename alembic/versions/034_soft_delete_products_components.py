"""Soft-delete flags for components and products.

Revision ID: 034
Revises: 033
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "components",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "components",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_components_is_deleted", "components", ["is_deleted"])

    op.add_column(
        "products",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "products",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_products_is_deleted", "products", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_products_is_deleted", table_name="products")
    op.drop_column("products", "deleted_at")
    op.drop_column("products", "is_deleted")
    op.drop_index("ix_components_is_deleted", table_name="components")
    op.drop_column("components", "deleted_at")
    op.drop_column("components", "is_deleted")
