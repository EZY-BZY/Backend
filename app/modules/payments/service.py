"""Payment service. Public API of payments module."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.payments.models import Payment
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import PaymentCreate


class PaymentService:
    def __init__(self, db: Session) -> None:
        self._repo = PaymentRepository(db)

    def get_by_id(self, payment_id: UUID | str, company_id: UUID | str) -> Payment | None:
        return self._repo.get_by_id(payment_id, company_id)

    def create(
        self,
        from_company_id: UUID | str,
        created_by_user_id: UUID | str | None,
        data: PaymentCreate,
    ) -> Payment:
        payment = Payment(
            from_company_id=str(from_company_id),
            to_company_id=str(data.to_company_id),
            invoice_id=str(data.invoice_id) if data.invoice_id else None,
            created_by_user_id=str(created_by_user_id) if created_by_user_id else None,
            amount=data.amount,
            currency=data.currency,
            reference=data.reference,
            note=data.note,
        )
        return self._repo.create(payment)

    def list_by_company(
        self, company_id: UUID | str, *, skip: int = 0, limit: int = 100
    ) -> list[Payment]:
        return self._repo.list_by_company(company_id, skip=skip, limit=limit)
