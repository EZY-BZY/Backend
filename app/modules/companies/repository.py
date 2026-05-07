"""Data access for companies."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.companies.models import Company


class CompanyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_company_by_id(self, company_id: str) -> Company | None:
        return self.db.get(Company, company_id)

    def list_companies(self) -> list[Company]:
        stmt = select(Company).order_by(Company.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def list_companies_for_owner(self, owner_id: str) -> list[Company]:
        stmt = (
            select(Company)
            .where(Company.owner_id == owner_id)
            .order_by(Company.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_company(self, row: Company) -> Company:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_company(self, row: Company) -> Company:
        self.db.commit()
        self.db.refresh(row)
        return row
