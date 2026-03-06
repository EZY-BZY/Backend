"""Ledger routes. Mount under /api/v1."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.modules.ledger.dependencies import LedgerServiceDep
from app.modules.ledger.schemas import LedgerEntryCreate, LedgerEntryRead

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.post("", response_model=LedgerEntryRead)
def create_ledger_entry(data: LedgerEntryCreate, service: LedgerServiceDep):
    """Create ledger entry. In production: from_company_id and user from auth."""
    raise HTTPException(status_code=501, detail="Require company and user context")


@router.get("/{entry_id}", response_model=LedgerEntryRead)
def get_ledger_entry(entry_id: UUID, service: LedgerServiceDep):
    """Get ledger entry (tenant-scoped)."""
    entry = service.get_by_id(entry_id, "00000000-0000-0000-0000-000000000000")
    if not entry:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    return LedgerEntryRead(
        id=UUID(entry.id),
        from_company_id=UUID(entry.from_company_id),
        to_company_id=UUID(entry.to_company_id),
        source_type=entry.source_type,
        source_id=UUID(entry.source_id) if entry.source_id else None,
        amount=entry.amount,
        currency=entry.currency,
        created_by_user_id=UUID(entry.created_by_user_id) if entry.created_by_user_id else None,
        note=entry.note,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat(),
    )


@router.get("/balance/{from_company_id}/{to_company_id}")
def get_balance(
    from_company_id: UUID,
    to_company_id: UUID,
    currency: str = "USD",
    service: LedgerServiceDep,
) -> dict:
    """Balance that from_company owes to_company (positive = debt)."""
    bal = service.balance_between(from_company_id, to_company_id, currency)
    return {"from_company_id": str(from_company_id), "to_company_id": str(to_company_id), "balance": bal, "currency": currency}
