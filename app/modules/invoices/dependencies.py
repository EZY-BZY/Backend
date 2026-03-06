"""Invoices module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.invoices.service import InvoiceService


def get_invoice_service(db: DbSession) -> InvoiceService:
    return InvoiceService(db)


InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
