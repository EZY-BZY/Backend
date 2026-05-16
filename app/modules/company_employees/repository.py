"""Data access for company employees."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.modules.company_employees.models import (
    CompanyEmployee,
    CompanyEmployeeBranch,
    CompanyEmployeePhone,
    EmployeeAppPermission,
)


class CompanyEmployeeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _employee_load_options(self):
        return (
            selectinload(CompanyEmployee.phones),
            selectinload(CompanyEmployee.app_permissions).selectinload(EmployeeAppPermission.app_permission),
            selectinload(CompanyEmployee.branch_assignments).selectinload(CompanyEmployeeBranch.branch),
        )

    def get_employee(self, employee_id: str, *, load_children: bool = False) -> CompanyEmployee | None:
        if not load_children:
            return self.db.get(CompanyEmployee, employee_id)
        stmt = (
            select(CompanyEmployee)
            .where(CompanyEmployee.id == employee_id)
            .options(*self._employee_load_options())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_employee_by_active_phone(self, normalized_phone: str) -> CompanyEmployee | None:
        stmt = (
            select(CompanyEmployee)
            .join(CompanyEmployeePhone, CompanyEmployeePhone.employee_id == CompanyEmployee.id)
            .where(
                CompanyEmployeePhone.phone_number == normalized_phone,
                CompanyEmployeePhone.is_active.is_(True),
                CompanyEmployee.is_active.is_(True),
                CompanyEmployee.is_deleted.is_(False),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_branch(
        self,
        company_id: str,
        branch_id: str,
        *,
        load_children: bool = True,
        active_employees_only: bool = False,
    ) -> list[CompanyEmployee]:
        """Filter by branch via subquery (avoid join + selectinload duplicating ``branch_assignments``)."""
        assigned = select(CompanyEmployeeBranch.employee_id).where(
            CompanyEmployeeBranch.branch_id == branch_id,
        )
        stmt = select(CompanyEmployee).where(
            CompanyEmployee.company_id == company_id,
            CompanyEmployee.id.in_(assigned),
        )
        if active_employees_only:
            stmt = stmt.where(
                CompanyEmployee.is_active.is_(True),
                CompanyEmployee.is_deleted.is_(False),
            )
        if load_children:
            stmt = stmt.options(*self._employee_load_options())
        stmt = stmt.order_by(CompanyEmployee.is_deleted.asc(), CompanyEmployee.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_branch_assignment(self, employee_id: str, branch_id: str) -> CompanyEmployeeBranch | None:
        stmt = select(CompanyEmployeeBranch).where(
            CompanyEmployeeBranch.employee_id == employee_id,
            CompanyEmployeeBranch.branch_id == branch_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_company(self, company_id: str, *, load_children: bool = False) -> list[CompanyEmployee]:
        stmt = select(CompanyEmployee).where(CompanyEmployee.company_id == company_id)
        if load_children:
            stmt = stmt.options(*self._employee_load_options())
        stmt = stmt.order_by(CompanyEmployee.is_deleted.asc(), CompanyEmployee.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def list_filtered(
        self,
        *,
        company_id: str | None = None,
        role: str | None = None,
        department: str | None = None,
        is_active: bool | None = None,
    ) -> list[CompanyEmployee]:
        stmt = select(CompanyEmployee).options(*self._employee_load_options())
        if company_id is not None:
            stmt = stmt.where(CompanyEmployee.company_id == company_id)
        if role is not None:
            stmt = stmt.where(CompanyEmployee.role == role)
        if department is not None:
            stmt = stmt.where(CompanyEmployee.department == department)
        if is_active is not None:
            stmt = stmt.where(CompanyEmployee.is_active == is_active)
        stmt = stmt.order_by(
            CompanyEmployee.company_id.asc(),
            CompanyEmployee.is_deleted.asc(),
            CompanyEmployee.name.asc(),
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_employee(self, row: CompanyEmployee) -> CompanyEmployee:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_employee(self, row: CompanyEmployee) -> CompanyEmployee:
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_phone(self, phone_id: str) -> CompanyEmployeePhone | None:
        return self.db.get(CompanyEmployeePhone, phone_id)

    def get_permission_link(self, employee_id: str, app_permission_id: str) -> EmployeeAppPermission | None:
        stmt = select(EmployeeAppPermission).where(
            EmployeeAppPermission.employee_id == employee_id,
            EmployeeAppPermission.app_permission_id == app_permission_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_permission_link_loaded(
        self, employee_id: str, app_permission_id: str
    ) -> EmployeeAppPermission | None:
        stmt = (
            select(EmployeeAppPermission)
            .where(
                EmployeeAppPermission.employee_id == employee_id,
                EmployeeAppPermission.app_permission_id == app_permission_id,
            )
            .options(selectinload(EmployeeAppPermission.app_permission))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_phone(self, row: CompanyEmployeePhone) -> CompanyEmployeePhone:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_phone(self, row: CompanyEmployeePhone) -> CompanyEmployeePhone:
        self.db.commit()
        self.db.refresh(row)
        return row

    def create_permission_link(self, row: EmployeeAppPermission) -> EmployeeAppPermission:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_permission_link(self, row: EmployeeAppPermission) -> EmployeeAppPermission:
        self.db.commit()
        self.db.refresh(row)
        return row

    def clear_primary_phones(self, employee_id: str, *, except_phone_id: str | None = None) -> None:
        stmt = update(CompanyEmployeePhone).where(CompanyEmployeePhone.employee_id == employee_id)
        if except_phone_id is not None:
            stmt = stmt.where(CompanyEmployeePhone.id != except_phone_id)
        stmt = stmt.values(is_primary=False)
        self.db.execute(stmt)
