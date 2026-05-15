"""Data access for company_financials_accounts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.company_financials_accounts.models import CompanyFinancialsAccount


class CompanyFinancialsAccountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _with_catalog(self):
        return joinedload(CompanyFinancialsAccount.bank_and_wallet)

    def get_by_id(self, row_id: str, *, load_catalog: bool = False) -> CompanyFinancialsAccount | None:
        if not load_catalog:
            return self.db.get(CompanyFinancialsAccount, row_id)
        stmt = (
            select(CompanyFinancialsAccount)
            .where(CompanyFinancialsAccount.id == row_id)
            .options(self._with_catalog())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_company(self, company_id: str, *, load_catalog: bool = False) -> list[CompanyFinancialsAccount]:
        stmt = (
            select(CompanyFinancialsAccount)
            .where(CompanyFinancialsAccount.company_id == company_id)
            .order_by(CompanyFinancialsAccount.created_at.desc())
        )
        if load_catalog:
            stmt = stmt.options(self._with_catalog())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, row: CompanyFinancialsAccount) -> CompanyFinancialsAccount:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: CompanyFinancialsAccount) -> CompanyFinancialsAccount:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: CompanyFinancialsAccount) -> None:
        self.db.delete(row)
        self.db.commit()
