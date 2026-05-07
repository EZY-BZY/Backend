"""Business logic for company contact info."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.companies.service import CompanyService
from app.modules.company_contact_info.models import CompanyContactInfo
from app.modules.company_contact_info.repository import CompanyContactInfoRepository
from app.modules.company_contact_info.schemas import CompanyContactInfoCreate, CompanyContactInfoUpdate


class CompanyContactInfoService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyContactInfoRepository(db)
        self._companies = CompanyService(db)

    def list_for_company_admin(self, company_id: str) -> list[CompanyContactInfo] | None:
        if self._companies.get_company_by_id(company_id) is None:
            return None
        return self._repo.list_for_company(company_id)

    def get_for_company_admin(
        self,
        company_id: str,
        contact_id: str,
    ) -> CompanyContactInfo | None:
        if self._companies.get_company_by_id(company_id) is None:
            return None
        row = self._repo.get_by_id(contact_id)
        if row is None or row.company_id != company_id:
            return None
        return row

    def list_for_owner(self, company_id: str, owner_id: str) -> list[CompanyContactInfo] | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        return self._repo.list_for_company(company_id)

    def get_for_owner(
        self,
        company_id: str,
        contact_id: str,
        owner_id: str,
    ) -> CompanyContactInfo | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        row = self._repo.get_by_id(contact_id)
        if row is None or row.company_id != company_id:
            return None
        return row

    def create(
        self,
        company_id: str,
        owner_id: str,
        data: CompanyContactInfoCreate,
    ) -> CompanyContactInfo:
        if self._companies.get_company(company_id, owner_id) is None:
            raise ValueError("Company not found or not owned by you.")
        row = CompanyContactInfo(
            company_id=company_id,
            title=data.title,
            value=data.value,
            contact_type=data.contact_type.value,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create contact info.") from e

    def update(
        self,
        company_id: str,
        contact_id: str,
        owner_id: str,
        data: CompanyContactInfoUpdate,
    ) -> CompanyContactInfo | None:
        row = self.get_for_owner(company_id, contact_id, owner_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        if "contact_type" in payload and payload["contact_type"] is not None:
            row.contact_type = payload["contact_type"].value
            del payload["contact_type"]
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            return self._repo.update(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update contact info.") from e

    def delete(self, company_id: str, contact_id: str, owner_id: str) -> bool:
        row = self._repo.get_by_id(contact_id)
        if row is None or self._companies.get_company(company_id, owner_id) is None:
            return False
        if row.company_id != company_id:
            return False
        self._repo.delete(row)
        return True
