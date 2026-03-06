"""Product repository. Internal to products module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.products.models import Product


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: UUID | str, company_id: UUID | str) -> Product | None:
        """Get product by id; ensure it belongs to company (tenant isolation)."""
        product = self.db.get(Product, str(product_id))
        if product and str(product.company_id) == str(company_id):
            return product
        return None

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.commit()
        self.db.refresh(product)
        return product

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[Product]:
        stmt = select(Product).where(Product.company_id == str(company_id))
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
