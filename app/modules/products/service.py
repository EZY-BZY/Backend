"""Product service. Public API of products module."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: Session) -> None:
        self._repo = ProductRepository(db)

    def get_by_id(self, product_id: UUID | str, company_id: UUID | str) -> Product | None:
        return self._repo.get_by_id(product_id, company_id)

    def create(self, company_id: UUID | str, data: ProductCreate) -> Product:
        product = Product(
            company_id=str(company_id),
            name=data.name,
            sku=data.sku,
            description=data.description,
            unit_price=data.unit_price,
            currency=data.currency,
            is_active=data.is_active,
        )
        return self._repo.create(product)

    def update(
        self, product_id: UUID | str, company_id: UUID | str, data: ProductUpdate
    ) -> Product | None:
        product = self._repo.get_by_id(product_id, company_id)
        if not product:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(product, k, v)
        return self._repo.update(product)

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[Product]:
        return self._repo.list_by_company(company_id, skip=skip, limit=limit, active_only=active_only)
