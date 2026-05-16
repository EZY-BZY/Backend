"""Data access for organisation structure."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.company_employees.models import CompanyEmployee
from app.modules.organisation_structure.models import OrganisationStructure


class OrganisationStructureRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, structure_id: str) -> OrganisationStructure | None:
        return self.db.get(OrganisationStructure, structure_id)

    def get_for_company(self, company_id: str, structure_id: str) -> OrganisationStructure | None:
        row = self.get_by_id(structure_id)
        if row is None or str(row.company_id) != str(company_id):
            return None
        return row

    def list_for_company(
        self,
        company_id: str,
        *,
        search: str | None = None,
        include_deleted: bool = True,
    ) -> list[OrganisationStructure]:
        stmt = select(OrganisationStructure).where(OrganisationStructure.company_id == company_id)
        if not include_deleted:
            stmt = stmt.where(OrganisationStructure.is_deleted.is_(False))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    OrganisationStructure.name_en.ilike(term),
                    OrganisationStructure.name_ar.ilike(term),
                )
            )
        stmt = stmt.order_by(
            OrganisationStructure.is_deleted.asc(),
            OrganisationStructure.name_en.asc(),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_for_company_paginated(
        self,
        company_id: str,
        *,
        skip: int,
        limit: int,
        search: str | None = None,
        include_deleted: bool = True,
    ) -> tuple[list[OrganisationStructure], int]:
        base = select(OrganisationStructure).where(OrganisationStructure.company_id == company_id)
        if not include_deleted:
            base = base.where(OrganisationStructure.is_deleted.is_(False))
        if search:
            term = f"%{search.strip()}%"
            base = base.where(
                or_(
                    OrganisationStructure.name_en.ilike(term),
                    OrganisationStructure.name_ar.ilike(term),
                )
            )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int(self.db.execute(count_stmt).scalar_one())

        stmt = (
            base.order_by(
                OrganisationStructure.is_deleted.asc(),
                OrganisationStructure.name_en.asc(),
            )
            .offset(skip)
            .limit(limit)
        )
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def count_assigned_employees(self, structure_id: str, *, include_inactive: bool = False) -> int:
        stmt = select(func.count()).select_from(CompanyEmployee).where(
            CompanyEmployee.organisation_structure_id == structure_id,
            CompanyEmployee.is_deleted.is_(False),
        )
        if not include_inactive:
            stmt = stmt.where(CompanyEmployee.is_active.is_(True))
        return int(self.db.execute(stmt).scalar_one())

    def compute_employee_totals(self, structure_id: str) -> tuple[int, Decimal]:
        stmt = select(
            func.count(CompanyEmployee.id),
            func.coalesce(
                func.sum(
                    func.coalesce(CompanyEmployee.salary, 0) + CompanyEmployee.bonus_amount
                ),
                0,
            ),
        ).where(
            CompanyEmployee.organisation_structure_id == structure_id,
            CompanyEmployee.is_deleted.is_(False),
            CompanyEmployee.is_active.is_(True),
        )
        count, salaries = self.db.execute(stmt).one()
        return int(count or 0), Decimal(str(salaries or 0))

    def recompute_and_save_totals(
        self,
        structure_id: str,
        *,
        commit: bool = True,
    ) -> OrganisationStructure | None:
        row = self.get_by_id(structure_id)
        if row is None:
            return None
        total_employees, total_salaries = self.compute_employee_totals(structure_id)
        row.total_employees = total_employees
        row.total_salaries = float(total_salaries)
        if commit:
            self.db.commit()
            self.db.refresh(row)
        else:
            self.db.flush()
        return row

    def create(self, row: OrganisationStructure) -> OrganisationStructure:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: OrganisationStructure) -> OrganisationStructure:
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_ids_for_company(self, company_id: str) -> list[str]:
        stmt = select(OrganisationStructure.id).where(OrganisationStructure.company_id == company_id)
        return [str(x) for x in self.db.execute(stmt).scalars().all()]

    def sum_department_totals_for_company(
        self,
        company_id: str,
        *,
        include_deleted: bool = False,
    ) -> tuple[int, float]:
        """Sum ``total_employees`` and ``total_salaries`` across all departments in the company."""
        stmt = select(
            func.coalesce(func.sum(OrganisationStructure.total_employees), 0),
            func.coalesce(func.sum(OrganisationStructure.total_salaries), 0),
        ).where(OrganisationStructure.company_id == company_id)
        if not include_deleted:
            stmt = stmt.where(OrganisationStructure.is_deleted.is_(False))
        employees, salaries = self.db.execute(stmt).one()
        return int(employees or 0), float(salaries or 0)
