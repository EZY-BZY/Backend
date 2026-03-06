"""Payment routes. Mount under /api/v1."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.modules.payments.dependencies import PaymentServiceDep
from app.modules.payments.schemas import PaymentCreate, PaymentRead

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentRead)
def create_payment(data: PaymentCreate, service: PaymentServiceDep):
    """Create payment. In production: from_company_id and user from auth."""
    raise HTTPException(status_code=501, detail="Require company and user context")


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: UUID, service: PaymentServiceDep):
    """Get payment (from_company or to_company)."""
    p = service.get_by_id(payment_id, "00000000-0000-0000-0000-000000000000")
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentRead(
        id=UUID(p.id),
        from_company_id=UUID(p.from_company_id),
        to_company_id=UUID(p.to_company_id),
        invoice_id=UUID(p.invoice_id) if p.invoice_id else None,
        created_by_user_id=UUID(p.created_by_user_id) if p.created_by_user_id else None,
        amount=p.amount,
        currency=p.currency,
        reference=p.reference,
        note=p.note,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )
