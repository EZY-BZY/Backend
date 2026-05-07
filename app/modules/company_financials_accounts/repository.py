"""Data access for company_financials_accounts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_financials_accounts.models import CompanyFinancialsAccount


class CompanyFinancialsAccountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, row_id: str) -> CompanyFinancialsAccount | None:
        return self.db.get(CompanyFinancialsAccount, row_id)

    def list_for_company(self, company_id: str) -> list[CompanyFinancialsAccount]:
        stmt = (
            select(CompanyFinancialsAccount)
            .where(CompanyFinancialsAccount.company_id == company_id)
            .order_by(CompanyFinancialsAccount.created_at.desc())
        )
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
