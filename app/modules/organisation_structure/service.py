"""Business logic for organisation structure."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.modules.clients_auth.dependencies import CurrentClient
from app.modules.companies.service import CompanyService
from app.modules.company_employees.dependencies import ensure_employer_manage_access
from app.modules.organisation_structure.models import OrganisationStructure
from app.modules.organisation_structure.repository import OrganisationStructureRepository
from app.modules.organisation_structure.schemas import (
    OrganisationStructureCreate,
    OrganisationStructureUpdate,
)


class OrganisationStructureService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = OrganisationStructureRepository(db)

    def _actor_id(self, current: CurrentClient) -> str:
        return str(current["user_id"])

    def create(
        self,
        company_id: str,
        current: CurrentClient,
        data: OrganisationStructureCreate,
    ) -> OrganisationStructure:
        ensure_employer_manage_access(self._db, current, company_id)
        actor = self._actor_id(current)
        row = OrganisationStructure(
            company_id=company_id,
            name_en=data.name_en,
            name_ar=data.name_ar,
            description=data.description,
            department_establish_date=data.department_establish_date,
            total_salaries=0,
            total_employees=0,
            created_by=actor,
            updated_by=actor,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create organisation structure.") from e

    def list_paginated(
        self,
        company_id: str,
        current: CurrentClient,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[OrganisationStructure], int] | None:
        if CompanyService(self._db).get_company_by_id(company_id) is None:
            return None
        ensure_employer_manage_access(self._db, current, company_id)
        skip = (page - 1) * page_size
        return self._repo.list_for_company_paginated(
            company_id,
            skip=skip,
            limit=page_size,
            search=search,
            include_deleted=True,
        )

    def get_by_id(
        self,
        company_id: str,
        structure_id: str,
        current: CurrentClient,
    ) -> OrganisationStructure | None:
        ensure_employer_manage_access(self._db, current, company_id)
        return self._repo.get_for_company(company_id, structure_id)

    def update(
        self,
        company_id: str,
        structure_id: str,
        current: CurrentClient,
        data: OrganisationStructureUpdate,
    ) -> OrganisationStructure | None:
        ensure_employer_manage_access(self._db, current, company_id)
        row = self._repo.get_for_company(company_id, structure_id)
        if row is None:
            return None
        if row.is_deleted:
            raise ValueError("Cannot update a deleted organisation structure.")
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        for key, value in payload.items():
            setattr(row, key, value)
        row.updated_by = self._actor_id(current)
        try:
            return self._repo.save(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update organisation structure.") from e

    def delete(
        self,
        company_id: str,
        structure_id: str,
        current: CurrentClient,
    ) -> bool:
        ensure_employer_manage_access(self._db, current, company_id)
        row = self._repo.get_for_company(company_id, structure_id)
        if row is None:
            return False
        if row.is_deleted:
            return True
        assigned = self._repo.count_assigned_employees(structure_id, include_inactive=True)
        if assigned > 0:
            raise ValueError(
                "Cannot delete organisation structure while employees are still assigned to it."
            )
        row.is_deleted = True
        row.deleted_at = utc_now()
        row.updated_by = self._actor_id(current)
        row.total_employees = 0
        row.total_salaries = 0
        self._repo.save(row)
        return True

    def recalculate_totals(
        self,
        company_id: str,
        structure_id: str,
        current: CurrentClient,
    ) -> OrganisationStructure | None:
        ensure_employer_manage_access(self._db, current, company_id)
        if self._repo.get_for_company(company_id, structure_id) is None:
            return None
        return self._repo.recompute_and_save_totals(structure_id)

    def recalculate_all_for_company(
        self,
        company_id: str,
        current: CurrentClient,
    ) -> int:
        ensure_employer_manage_access(self._db, current, company_id)
        if CompanyService(self._db).get_company_by_id(company_id) is None:
            raise ValueError("Company not found.")
        count = 0
        for sid in self._repo.list_ids_for_company(company_id):
            self._repo.recompute_and_save_totals(sid)
            count += 1
        return count
