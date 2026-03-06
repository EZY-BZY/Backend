"""Payment repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.payments.models import Payment


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self, payment_id: UUID | str, company_id: UUID | str
    ) -> Payment | None:
        """Get payment; company_id can be from_company or to_company."""
        p = self.db.get(Payment, str(payment_id))
        if not p:
            return None
        if str(p.from_company_id) != str(company_id) and str(p.to_company_id) != str(company_id):
            return None
        return p

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def list_by_company(
        self, company_id: UUID | str, *, skip: int = 0, limit: int = 100
    ) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(
                (Payment.from_company_id == str(company_id))
                | (Payment.to_company_id == str(company_id))
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
