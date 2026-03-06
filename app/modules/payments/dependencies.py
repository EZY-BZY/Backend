"""Payments module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.payments.service import PaymentService


def get_payment_service(db: DbSession) -> PaymentService:
    return PaymentService(db)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
