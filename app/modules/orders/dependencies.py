"""Orders module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.orders.service import OrderService


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(db)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
