"""Order repository. Internal to orders module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.orders.models import Order, OrderItem


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self, order_id: UUID | str, company_id: UUID | str
    ) -> Order | None:
        """Get order by id; ensure buyer_company_id matches (tenant isolation)."""
        order = self.db.get(Order, str(order_id))
        if order and str(order.buyer_company_id) == str(company_id):
            return order
        return None

    def create(self, order: Order, items: list[OrderItem]) -> Order:
        self.db.add(order)
        self.db.flush()
        for item in items:
            item.order_id = order.id
            self.db.add(item)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_by_buyer(
        self,
        buyer_company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.buyer_company_id == str(buyer_company_id))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
