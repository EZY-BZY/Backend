"""Invoice repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.invoices.models import Invoice


class InvoiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self, invoice_id: UUID | str, company_id: UUID | str
    ) -> Invoice | None:
        """Get invoice; company_id can be seller or buyer for isolation."""
        inv = self.db.get(Invoice, str(invoice_id))
        if not inv:
            return None
        if str(inv.seller_company_id) != str(company_id) and str(inv.buyer_company_id) != str(company_id):
            return None
        return inv

    def create(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def list_by_seller(
        self, seller_company_id: UUID | str, *, skip: int = 0, limit: int = 100
    ) -> list[Invoice]:
        stmt = (
            select(Invoice)
            .where(Invoice.seller_company_id == str(seller_company_id))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
