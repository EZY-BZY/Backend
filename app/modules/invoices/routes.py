"""Invoice routes. Mount under /api/v1."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.modules.invoices.dependencies import InvoiceServiceDep
from app.modules.invoices.schemas import InvoiceCreate, InvoiceRead

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceRead)
def create_invoice(data: InvoiceCreate, service: InvoiceServiceDep):
    """Create invoice. In production: seller_company_id and user from auth."""
    raise HTTPException(status_code=501, detail="Require company and user context")


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: UUID, service: InvoiceServiceDep):
    """Get invoice (seller or buyer company)."""
    inv = service.get_by_id(invoice_id, "00000000-0000-0000-0000-000000000000")
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceRead(
        id=UUID(inv.id),
        seller_company_id=UUID(inv.seller_company_id),
        buyer_company_id=UUID(inv.buyer_company_id),
        order_id=UUID(inv.order_id) if inv.order_id else None,
        created_by_user_id=UUID(inv.created_by_user_id) if inv.created_by_user_id else None,
        status=inv.status,
        total_amount=inv.total_amount,
        currency=inv.currency,
        reference=inv.reference,
        note=inv.note,
        created_at=inv.created_at.isoformat(),
        updated_at=inv.updated_at.isoformat(),
    )
