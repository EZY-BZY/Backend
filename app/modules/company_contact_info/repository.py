"""Data access for company_contact_infos."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_contact_info.models import CompanyContactInfo


class CompanyContactInfoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, row_id: str) -> CompanyContactInfo | None:
        return self.db.get(CompanyContactInfo, row_id)

    def list_for_company(self, company_id: str) -> list[CompanyContactInfo]:
        stmt = (
            select(CompanyContactInfo)
            .where(CompanyContactInfo.company_id == company_id)
            .order_by(CompanyContactInfo.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, row: CompanyContactInfo) -> CompanyContactInfo:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: CompanyContactInfo) -> CompanyContactInfo:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: CompanyContactInfo) -> None:
        self.db.delete(row)
        self.db.commit()
