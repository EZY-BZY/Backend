"""Data access for companies."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.companies.models import Company, CompanyIndustry


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

    def create_company(self, row: Company, industry_ids: list[str]) -> Company:
        self.db.add(row)
        self.db.flush()
        self.db.refresh(row)
        for iid in industry_ids:
            self.db.add(CompanyIndustry(company_id=row.id, industry_id=iid))
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_company(self, row: Company) -> Company:
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_industry_ids_for_company(self, company_id: str) -> list[str]:
        stmt = (
            select(CompanyIndustry.industry_id)
            .where(CompanyIndustry.company_id == company_id)
            .order_by(CompanyIndustry.industry_id.asc())
        )
        return [str(x) for x in self.db.execute(stmt).scalars().all()]

    def list_industry_ids_by_company_ids(self, company_ids: list[str]) -> dict[str, list[str]]:
        if not company_ids:
            return {}
        stmt = (
            select(CompanyIndustry.company_id, CompanyIndustry.industry_id)
            .where(CompanyIndustry.company_id.in_(company_ids))
            .order_by(CompanyIndustry.company_id.asc(), CompanyIndustry.industry_id.asc())
        )
        out: dict[str, list[str]] = {cid: [] for cid in company_ids}
        for cid, iid in self.db.execute(stmt).all():
            out[str(cid)].append(str(iid))
        return out

    def replace_company_industries(self, company_id: str, industry_ids: list[str]) -> None:
        self.db.execute(delete(CompanyIndustry).where(CompanyIndustry.company_id == company_id))
        for iid in industry_ids:
            self.db.add(CompanyIndustry(company_id=company_id, industry_id=iid))
        self.db.commit()
