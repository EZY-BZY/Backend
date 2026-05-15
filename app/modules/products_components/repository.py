"""Data access for products & components."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.products_components.models import (
    Component,
    ComponentBranchQuantity,
    Product,
    ProductBranchQuantity,
    ProductComponent,
)


class ProductsComponentsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Components ---

    def list_components(self, company_id: str, *, active_only: bool = True) -> list[Component]:
        stmt = select(Component).where(Component.company_id == company_id)
        if active_only:
            stmt = stmt.where(Component.is_active.is_(True))
        stmt = stmt.order_by(Component.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def list_components_paginated(
        self,
        company_id: str,
        *,
        skip: int,
        limit: int,
        active_only: bool = True,
    ) -> tuple[list[Component], int]:
        base = select(Component).where(Component.company_id == company_id)
        if active_only:
            base = base.where(Component.is_active.is_(True))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int(self.db.execute(count_stmt).scalar_one())

        stmt = base.order_by(Component.created_at.desc()).offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def get_component(self, component_id: str) -> Component | None:
        return self.db.get(Component, component_id)

    def create_component(self, row: Component) -> Component:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_component(self, row: Component) -> Component:
        self.db.commit()
        self.db.refresh(row)
        return row

    # --- Products ---

    def list_products(self, company_id: str, *, active_only: bool = True) -> list[Product]:
        stmt = select(Product).where(Product.company_id == company_id)
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        stmt = stmt.order_by(Product.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def list_products_paginated(
        self,
        company_id: str,
        *,
        skip: int,
        limit: int,
        active_only: bool = True,
        visible_to_public_only: bool = False,
    ) -> tuple[list[Product], int]:
        base = select(Product).where(Product.company_id == company_id)
        if active_only:
            base = base.where(Product.is_active.is_(True))
        if visible_to_public_only:
            base = base.where(Product.show_product.is_(True))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int(self.db.execute(count_stmt).scalar_one())

        stmt = base.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def get_product(self, product_id: str, *, load_children: bool = False) -> Product | None:
        if not load_children:
            return self.db.get(Product, product_id)
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.branch_quantities),
                selectinload(Product.component_links).selectinload(ProductComponent.component),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_product(self, row: Product) -> Product:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_product(self, row: Product) -> Product:
        self.db.commit()
        self.db.refresh(row)
        return row

    # --- Component branch quantities ---

    def list_component_branch_quantities(
        self,
        component_id: str,
    ) -> list[ComponentBranchQuantity]:
        stmt = (
            select(ComponentBranchQuantity)
            .where(ComponentBranchQuantity.component_id == component_id)
            .order_by(ComponentBranchQuantity.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_component_branch_quantity(self, row_id: str) -> ComponentBranchQuantity | None:
        return self.db.get(ComponentBranchQuantity, row_id)

    def get_component_branch_quantity_by_pair(
        self,
        component_id: str,
        branch_id: str,
    ) -> ComponentBranchQuantity | None:
        stmt = select(ComponentBranchQuantity).where(
            ComponentBranchQuantity.component_id == component_id,
            ComponentBranchQuantity.branch_id == branch_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_component_branch_quantity(
        self,
        row: ComponentBranchQuantity,
    ) -> ComponentBranchQuantity:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_component_branch_quantity(
        self,
        row: ComponentBranchQuantity,
    ) -> ComponentBranchQuantity:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_component_branch_quantity(self, row: ComponentBranchQuantity) -> None:
        self.db.delete(row)
        self.db.commit()

    # --- Product branch quantities ---

    def list_product_branch_quantities(self, product_id: str) -> list[ProductBranchQuantity]:
        stmt = (
            select(ProductBranchQuantity)
            .where(ProductBranchQuantity.product_id == product_id)
            .order_by(ProductBranchQuantity.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_product_branch_quantity(self, row_id: str) -> ProductBranchQuantity | None:
        return self.db.get(ProductBranchQuantity, row_id)

    def get_product_branch_quantity_by_pair(
        self,
        product_id: str,
        branch_id: str,
    ) -> ProductBranchQuantity | None:
        stmt = select(ProductBranchQuantity).where(
            ProductBranchQuantity.product_id == product_id,
            ProductBranchQuantity.branch_id == branch_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_product_branch_quantity(self, row: ProductBranchQuantity) -> ProductBranchQuantity:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_product_branch_quantity(self, row: ProductBranchQuantity) -> ProductBranchQuantity:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_product_branch_quantity(self, row: ProductBranchQuantity) -> None:
        self.db.delete(row)
        self.db.commit()

    # --- Product components ---

    def list_product_components(self, product_id: str) -> list[ProductComponent]:
        stmt = (
            select(ProductComponent)
            .where(ProductComponent.product_id == product_id)
            .options(selectinload(ProductComponent.component))
            .order_by(ProductComponent.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_product_component(self, row_id: str) -> ProductComponent | None:
        stmt = (
            select(ProductComponent)
            .where(ProductComponent.id == row_id)
            .options(selectinload(ProductComponent.component))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_product_component_by_pair(
        self,
        product_id: str,
        component_id: str,
    ) -> ProductComponent | None:
        stmt = select(ProductComponent).where(
            ProductComponent.product_id == product_id,
            ProductComponent.component_id == component_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_product_component(self, row: ProductComponent) -> ProductComponent:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_product_component(self, row: ProductComponent) -> ProductComponent:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_product_component(self, row: ProductComponent) -> None:
        self.db.delete(row)
        self.db.commit()
