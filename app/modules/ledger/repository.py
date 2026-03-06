"""Ledger entry repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.ledger.models import LedgerEntry


class LedgerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self, entry_id: UUID | str, company_id: UUID | str
    ) -> LedgerEntry | None:
        """Get entry; company must be from_company or to_company."""
        entry = self.db.get(LedgerEntry, str(entry_id))
        if not entry:
            return None
        if str(entry.from_company_id) != str(company_id) and str(entry.to_company_id) != str(company_id):
            return None
        return entry

    def create(self, entry: LedgerEntry) -> LedgerEntry:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntry)
            .where(
                (LedgerEntry.from_company_id == str(company_id))
                | (LedgerEntry.to_company_id == str(company_id))
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def balance_between(
        self, from_company_id: UUID | str, to_company_id: UUID | str, currency: str = "USD"
    ) -> float:
        """Sum of entries from A to B minus from B to A (what A owes B)."""
        # Positive amount: from_company owes to_company
        credit = (
            self.db.execute(
                select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                    LedgerEntry.from_company_id == str(from_company_id),
                    LedgerEntry.to_company_id == str(to_company_id),
                    LedgerEntry.currency == currency,
                )
            ).scalar_one()
            or 0
        )
        debit = (
            self.db.execute(
                select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                    LedgerEntry.from_company_id == str(to_company_id),
                    LedgerEntry.to_company_id == str(from_company_id),
                    LedgerEntry.currency == currency,
                )
            ).scalar_one()
            or 0
        )
        return float(debit - credit)  # positive = from_company owes to_company
