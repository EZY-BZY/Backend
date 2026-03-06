"""Order service. Public API of orders module."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.orders.models import Order, OrderItem
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import OrderCreate, OrderUpdate


class OrderService:
    def __init__(self, db: Session) -> None:
        self._repo = OrderRepository(db)

    def get_by_id(self, order_id: UUID | str, company_id: UUID | str) -> Order | None:
        """Get order; company_id is buyer (tenant) for isolation."""
        return self._repo.get_by_id(order_id, company_id)

    def create(
        self,
        buyer_company_id: UUID | str,
        created_by_user_id: UUID | str | None,
        data: OrderCreate,
    ) -> Order:
        order = Order(
            buyer_company_id=str(buyer_company_id),
            seller_company_id=str(data.seller_company_id),
            created_by_user_id=str(created_by_user_id) if created_by_user_id else None,
            status="draft",
            reference=data.reference,
            note=data.note,
        )
        items = [
            OrderItem(
                product_id=str(item.product_id) if item.product_id else None,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                currency=item.currency,
            )
            for item in data.items
        ]
        return self._repo.create(order, items)

    def list_by_buyer(
        self,
        buyer_company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        return self._repo.list_by_buyer(buyer_company_id, skip=skip, limit=limit)
