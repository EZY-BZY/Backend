"""Business logic for companies."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.allenums import CompanyStatus
from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.schemas import (
    CompanyChangeVisibilityBody,
    CompanyCreate,
    CompanyUpdate,
)


class CompanyService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyRepository(db)

    def list_companies(self) -> list[Company]:
        return self._repo.list_companies()

    def get_company_by_id(self, company_id: str) -> Company | None:
        return self._repo.get_company_by_id(company_id)

    def get_company(self, company_id: str, owner_id: str) -> Company | None:
        row = self._repo.get_company_by_id(company_id)
        if row is None or row.owner_id != owner_id:
            return None
        return row

    def create_company(self, owner_id: str, data: CompanyCreate) -> Company:
        row = Company(
            owner_id=owner_id,
            company_name_ar=data.company_name_ar,
            company_name_en=data.company_name_en,
            company_description_ar=data.company_description_ar,
            company_description_en=data.company_description_en,
            show_branches=False,
            show_products=False,
            show_social_media=False,
            show_contact_info=False,
            status=CompanyStatus.ACTIVE.value,
            image=data.image,
            service=data.service.value,
            current_balance=data.current_balance,
            tax_number=data.tax_number,
        )
        try:
            return self._repo.create_company(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create company.") from e

    def update_company(self, company_id: str, owner_id: str, data: CompanyUpdate) -> Company | None:
        row = self.get_company(company_id, owner_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        if "service" in payload and payload["service"] is not None:
            row.service = payload["service"].value
            del payload["service"]
        if "status" in payload and payload["status"] is not None:
            row.status = payload["status"].value
            del payload["status"]
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            return self._repo.update_company(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update company.") from e

    def deactivate_company(self, company_id: str, owner_id: str) -> Company | None:
        row = self.get_company(company_id, owner_id)
        if row is None:
            return None
        row.status = CompanyStatus.INACTIVE.value
        return self._repo.update_company(row)

    def change_company_visibility(
        self,
        company_id: str,
        owner_id: str,
        body: CompanyChangeVisibilityBody,
    ) -> Company | None:
        row = self.get_company(company_id, owner_id)
        if row is None:
            return None
        row.show_products = body.show_products
        row.show_social_media = body.show_social_media
        row.show_contact_info = body.show_contact_info
        row.show_branches = body.show_branches
        return self._repo.update_company(row)
