"""products, components, branch quantities, product_components.

Revision ID: 031
Revises: 030
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "components",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name_ar", sa.String(256), nullable=False),
        sa.Column("name_other", sa.String(256), nullable=False),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column("description_other", sa.Text(), nullable=True),
        sa.Column("main_image", sa.String(2048), nullable=True),
        sa.Column("created_by_type", sa.String(32), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("updated_by_type", sa.String(32), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_components_created_by_type",
        ),
        sa.CheckConstraint(
            "updated_by_type IS NULL OR updated_by_type IN ('company_owner', 'employee')",
            name="ck_components_updated_by_type",
        ),
    )
    op.create_index("ix_components_company_id", "components", ["company_id"])

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name_ar", sa.String(256), nullable=False),
        sa.Column("name_other", sa.String(256), nullable=False),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column("description_other", sa.Text(), nullable=True),
        sa.Column("main_image", sa.String(2048), nullable=True),
        sa.Column("price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("show_price", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("show_product", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by_type", sa.String(32), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("updated_by_type", sa.String(32), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("price >= 0", name="ck_products_price_nonneg"),
        sa.CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_products_created_by_type",
        ),
        sa.CheckConstraint(
            "updated_by_type IS NULL OR updated_by_type IN ('company_owner', 'employee')",
            name="ck_products_updated_by_type",
        ),
    )
    op.create_index("ix_products_company_id", "products", ["company_id"])

    op.create_table(
        "component_branch_quantities",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["company_branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity >= 0", name="ck_component_branch_quantities_quantity_nonneg"),
        sa.UniqueConstraint("component_id", "branch_id", name="uq_component_branch_quantities_pair"),
    )
    op.create_index(
        "ix_component_branch_quantities_component_id",
        "component_branch_quantities",
        ["component_id"],
    )
    op.create_index(
        "ix_component_branch_quantities_branch_id",
        "component_branch_quantities",
        ["branch_id"],
    )

    op.create_table(
        "product_branch_quantities",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["company_branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity >= 0", name="ck_product_branch_quantities_quantity_nonneg"),
        sa.UniqueConstraint("product_id", "branch_id", name="uq_product_branch_quantities_pair"),
    )
    op.create_index(
        "ix_product_branch_quantities_product_id",
        "product_branch_quantities",
        ["product_id"],
    )
    op.create_index(
        "ix_product_branch_quantities_branch_id",
        "product_branch_quantities",
        ["branch_id"],
    )

    op.create_table(
        "product_components",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity > 0", name="ck_product_components_quantity_positive"),
        sa.UniqueConstraint("product_id", "component_id", name="uq_product_components_pair"),
    )
    op.create_index("ix_product_components_product_id", "product_components", ["product_id"])
    op.create_index("ix_product_components_component_id", "product_components", ["component_id"])


def downgrade() -> None:
    op.drop_index("ix_product_components_component_id", table_name="product_components")
    op.drop_index("ix_product_components_product_id", table_name="product_components")
    op.drop_table("product_components")
    op.drop_index("ix_product_branch_quantities_branch_id", table_name="product_branch_quantities")
    op.drop_index("ix_product_branch_quantities_product_id", table_name="product_branch_quantities")
    op.drop_table("product_branch_quantities")
    op.drop_index("ix_component_branch_quantities_branch_id", table_name="component_branch_quantities")
    op.drop_index("ix_component_branch_quantities_component_id", table_name="component_branch_quantities")
    op.drop_table("component_branch_quantities")
    op.drop_index("ix_products_company_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_components_company_id", table_name="components")
    op.drop_table("components")
