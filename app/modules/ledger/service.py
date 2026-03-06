"""Ledger service. Public API for ledger entries and balance queries."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.ledger.models import LedgerEntry
from app.modules.ledger.repository import LedgerRepository
from app.modules.ledger.schemas import LedgerEntryCreate


class LedgerService:
    def __init__(self, db: Session) -> None:
        self._repo = LedgerRepository(db)

    def get_by_id(self, entry_id: UUID | str, company_id: UUID | str) -> LedgerEntry | None:
        return self._repo.get_by_id(entry_id, company_id)

    def create_entry(
        self,
        from_company_id: UUID | str,
        created_by_user_id: UUID | str | None,
        data: LedgerEntryCreate,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            from_company_id=str(from_company_id),
            to_company_id=str(data.to_company_id),
            source_type=data.source_type,
            source_id=str(data.source_id) if data.source_id else None,
            amount=data.amount,
            currency=data.currency,
            created_by_user_id=str(created_by_user_id) if created_by_user_id else None,
            note=data.note,
        )
        return self._repo.create(entry)

    def list_by_company(
        self, company_id: UUID | str, *, skip: int = 0, limit: int = 100
    ) -> list[LedgerEntry]:
        return self._repo.list_by_company(company_id, skip=skip, limit=limit)

    def balance_between(
        self,
        from_company_id: UUID | str,
        to_company_id: UUID | str,
        currency: str = "USD",
    ) -> float:
        """Returns amount that from_company owes to_company (positive = debt)."""
        return self._repo.balance_between(from_company_id, to_company_id, currency)
