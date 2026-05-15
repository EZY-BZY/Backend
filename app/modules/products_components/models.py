"""Products, components, branch quantities, and product-component links."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Component(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Inventory component belonging to a company."""

    __tablename__ = "components"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    name_other: Mapped[str] = mapped_column(String(256), nullable=False)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_other: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_image: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    created_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    updated_by_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    branch_quantities: Mapped[list["ComponentBranchQuantity"]] = relationship(
        "ComponentBranchQuantity",
        back_populates="component",
        cascade="all, delete-orphan",
    )
    product_links: Mapped[list["ProductComponent"]] = relationship(
        "ProductComponent",
        back_populates="component",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_components_created_by_type",
        ),
        CheckConstraint(
            "updated_by_type IS NULL OR updated_by_type IN ('company_owner', 'employee')",
            name="ck_components_updated_by_type",
        ),
    )


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Sellable / catalog product belonging to a company."""

    __tablename__ = "products"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    name_other: Mapped[str] = mapped_column(String(256), nullable=False)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_other: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_image: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default="0")
    show_price: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    show_product: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    created_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    updated_by_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    branch_quantities: Mapped[list["ProductBranchQuantity"]] = relationship(
        "ProductBranchQuantity",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    component_links: Mapped[list["ProductComponent"]] = relationship(
        "ProductComponent",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_nonneg"),
        CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_products_created_by_type",
        ),
        CheckConstraint(
            "updated_by_type IS NULL OR updated_by_type IN ('company_owner', 'employee')",
            name="ck_products_updated_by_type",
        ),
    )


class ComponentBranchQuantity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stock of a component at a branch."""

    __tablename__ = "component_branch_quantities"

    component_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default="0")

    component: Mapped["Component"] = relationship("Component", back_populates="branch_quantities")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_component_branch_quantities_quantity_nonneg"),
        UniqueConstraint("component_id", "branch_id", name="uq_component_branch_quantities_pair"),
    )


class ProductBranchQuantity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stock of a product at a branch."""

    __tablename__ = "product_branch_quantities"

    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default="0")

    product: Mapped["Product"] = relationship("Product", back_populates="branch_quantities")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_product_branch_quantities_quantity_nonneg"),
        UniqueConstraint("product_id", "branch_id", name="uq_product_branch_quantities_pair"),
    )


class ProductComponent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Component required to build one unit of a product."""

    __tablename__ = "product_components"

    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="component_links")
    component: Mapped["Component"] = relationship("Component", back_populates="product_links")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_product_components_quantity_positive"),
        UniqueConstraint("product_id", "component_id", name="uq_product_components_pair"),
    )
