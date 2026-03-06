"""Invoice service. Public API of invoices module."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.invoices.models import Invoice
from app.modules.invoices.repository import InvoiceRepository
from app.modules.invoices.schemas import InvoiceCreate


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self._repo = InvoiceRepository(db)

    def get_by_id(self, invoice_id: UUID | str, company_id: UUID | str) -> Invoice | None:
        return self._repo.get_by_id(invoice_id, company_id)

    def create(
        self,
        seller_company_id: UUID | str,
        created_by_user_id: UUID | str | None,
        data: InvoiceCreate,
    ) -> Invoice:
        inv = Invoice(
            seller_company_id=str(seller_company_id),
            buyer_company_id=str(data.buyer_company_id),
            order_id=str(data.order_id) if data.order_id else None,
            created_by_user_id=str(created_by_user_id) if created_by_user_id else None,
            status="draft",
            total_amount=data.total_amount,
            currency=data.currency,
            reference=data.reference,
            note=data.note,
        )
        return self._repo.create(inv)

    def list_by_seller(
        self, seller_company_id: UUID | str, *, skip: int = 0, limit: int = 100
    ) -> list[Invoice]:
        return self._repo.list_by_seller(seller_company_id, skip=skip, limit=limit)
