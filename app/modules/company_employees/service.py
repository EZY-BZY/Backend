"""Business logic for company employees."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.allenums import CompanyAuditActorType
from app.core.security import get_password_hash, verify_password
from app.db.base import utc_now
from app.modules.app_permissions.models import AppPermission
from app.modules.clients_auth.dependencies import CurrentClient
from app.modules.company_employees.dependencies import ensure_employer_manage_access
from app.modules.company_branches.repository import CompanyBranchRepository
from app.modules.organisation_structure.recalc import refresh_organisation_structure_totals
from app.modules.organisation_structure.validation import ensure_organisation_structure_for_company
from app.modules.company_employees.models import (
    CompanyEmployee,
    CompanyEmployeeBranch,
    CompanyEmployeePhone,
    EmployeeAppPermission,
)
from app.modules.company_employees.repository import CompanyEmployeeRepository
from app.modules.company_employees.schemas import (
    CompanyEmployeeCreate,
    CompanyEmployeePhoneCreate,
    CompanyEmployeePhoneUpdate,
    CompanyEmployeeUpdate,
    normalize_phone,
)


def _audit_from_current(current: CurrentClient) -> tuple[str, str]:
    if current["account_type"] == "owner":
        return (CompanyAuditActorType.COMPANY_OWNER.value, current["user_id"])
    return (CompanyAuditActorType.EMPLOYEE.value, current["user_id"])


class CompanyEmployeeService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyEmployeeRepository(db)
        self._branches = CompanyBranchRepository(db)

    def get_by_id(self, employee_id: str, *, load_children: bool = False) -> CompanyEmployee | None:
        return self._repo.get_employee(employee_id, load_children=load_children)

    def authenticate_by_phone(self, phone: str, password: str) -> CompanyEmployee | None:
        try:
            normalized = normalize_phone(phone)
        except ValueError:
            return None
        emp = self._repo.get_employee_by_active_phone(normalized)
        if emp is None or emp.is_deleted or not verify_password(password, emp.password_hash):
            return None
        return emp

    def _get_for_company(self, company_id: str, employee_id: str, *, load_children: bool) -> CompanyEmployee | None:
        row = self._repo.get_employee(employee_id, load_children=load_children)
        if row is None or row.company_id != company_id:
            return None
        return row

    def _require_active_app_permission(self, app_permission_id: str) -> None:
        perm = self._db.get(AppPermission, app_permission_id)
        if perm is None or not perm.is_active:
            raise ValueError("One or more app permission ids are invalid or inactive.")

    def _add_or_reactivate_permission(
        self,
        employee_id: str,
        app_permission_id: str,
        actor_type: str,
        actor_id: str,
    ) -> None:
        self._require_active_app_permission(app_permission_id)
        link = self._repo.get_permission_link(employee_id, app_permission_id)
        if link is not None:
            if link.is_active:
                raise ValueError("Permission is already assigned to this employee.")
            link.is_active = True
            link.assigned_by_type = actor_type
            link.assigned_by_id = actor_id
            link.updated_by_type = actor_type
            link.updated_by_id = actor_id
            return
        self._db.add(
            EmployeeAppPermission(
                employee_id=employee_id,
                app_permission_id=app_permission_id,
                is_active=True,
                assigned_by_type=actor_type,
                assigned_by_id=actor_id,
                updated_by_type=actor_type,
                updated_by_id=actor_id,
            )
        )

    def _deactivate_permission(
        self,
        employee_id: str,
        app_permission_id: str,
        actor_type: str,
        actor_id: str,
    ) -> None:
        link = self._repo.get_permission_link(employee_id, app_permission_id)
        if link is None or not link.is_active:
            raise ValueError(f"No active assignment for app permission {app_permission_id}.")
        link.is_active = False
        link.updated_by_type = actor_type
        link.updated_by_id = actor_id

    def _require_branch_in_company(self, company_id: str, branch_id: str) -> None:
        branch = self._branches.get_branch(branch_id)
        if branch is None or str(branch.company_id) != str(company_id):
            raise ValueError(f"Branch {branch_id} not found for this company.")
        if branch.is_deleted:
            raise ValueError(f"Branch {branch_id} has been deleted.")

    def _assign_branch(
        self,
        employee_id: str,
        branch_id: str,
        company_id: str,
        actor_type: str,
        actor_id: str,
    ) -> None:
        self._require_branch_in_company(company_id, branch_id)
        if self._repo.get_branch_assignment(employee_id, branch_id) is not None:
            raise ValueError(f"Employee is already assigned to branch {branch_id}.")
        self._db.add(
            CompanyEmployeeBranch(
                employee_id=employee_id,
                branch_id=branch_id,
                created_by_type=actor_type,
                created_by_id=actor_id,
            )
        )

    def _unassign_branch(self, employee_id: str, branch_id: str) -> None:
        link = self._repo.get_branch_assignment(employee_id, branch_id)
        if link is None:
            raise ValueError(f"Employee is not assigned to branch {branch_id}.")
        self._db.delete(link)

    def create_employee(
        self,
        company_id: str,
        current: CurrentClient,
        data: CompanyEmployeeCreate,
    ) -> CompanyEmployee:
        ensure_employer_manage_access(self._db, current, company_id)
        org_id = str(data.organisation_structure_id) if data.organisation_structure_id else None
        ensure_organisation_structure_for_company(self._db, company_id, org_id)
        actor_type, actor_id = _audit_from_current(current)
        row = CompanyEmployee(
            company_id=company_id,
            name=data.name,
            email=data.email,
            password_hash=get_password_hash(data.password),
            salary=data.salary,
            bonus_amount=data.bonus_amount,
            salary_system=data.salary_system.value if data.salary_system else None,
            department=data.department,
            organisation_structure_id=org_id,
            role=data.role.value,
            is_active=True,
            created_by_type=actor_type,
            created_by_id=actor_id,
            updated_by_type=actor_type,
            updated_by_id=actor_id,
        )
        try:
            self._db.add(row)
            self._db.flush()
            for pid in data.app_permission_ids:
                self._add_or_reactivate_permission(str(row.id), str(pid), actor_type, actor_id)
            for bid in data.branch_ids:
                self._assign_branch(str(row.id), str(bid), company_id, actor_type, actor_id)
            refresh_organisation_structure_totals(self._db, org_id)
            self._db.commit()
            return self._repo.get_employee(str(row.id), load_children=True) or row
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create employee.") from e
        except ValueError:
            self._db.rollback()
            raise

    def list_employees_client(self, company_id: str, current: CurrentClient) -> list[CompanyEmployee]:
        ensure_employer_manage_access(self._db, current, company_id)
        return self._repo.list_for_company(company_id, load_children=True)

    def list_employees_by_branch(
        self,
        company_id: str,
        branch_id: str,
        current: CurrentClient,
    ) -> list[CompanyEmployee] | None:
        """Employees assigned to ``branch_id``; ``None`` if branch is not in this company."""
        ensure_employer_manage_access(self._db, current, company_id)
        branch = self._branches.get_branch(branch_id)
        if branch is None or str(branch.company_id) != str(company_id):
            return None
        return self._repo.list_for_branch(company_id, branch_id, load_children=True)

    def get_employee_client(self, company_id: str, employee_id: str, current: CurrentClient) -> CompanyEmployee | None:
        ensure_employer_manage_access(self._db, current, company_id)
        if self._get_for_company(company_id, employee_id, load_children=False) is None:
            return None
        # Reload with eager loads so branch_assignments are not polluted by prior join queries.
        return self._repo.get_employee(employee_id, load_children=True)

    def update_employee(
        self,
        company_id: str,
        employee_id: str,
        current: CurrentClient,
        data: CompanyEmployeeUpdate,
    ) -> CompanyEmployee | None:
        ensure_employer_manage_access(self._db, current, company_id)
        row = self._get_for_company(company_id, employee_id, load_children=False)
        if row is None:
            return None
        if row.is_deleted:
            raise ValueError("Cannot update a deleted employee.")
        previous_org_id = row.organisation_structure_id
        payload = data.model_dump(exclude_unset=True)
        new_ids = payload.pop("new_app_permission_ids", None)
        removed_ids = payload.pop("removed_app_permission_ids", None)
        new_branch_ids = payload.pop("new_branch_ids", None)
        removed_branch_ids = payload.pop("removed_branch_ids", None)
        perm_changes = new_ids is not None or removed_ids is not None
        branch_changes = new_branch_ids is not None or removed_branch_ids is not None
        if not payload and not perm_changes and not branch_changes:
            return self._repo.get_employee(employee_id, load_children=True)

        actor_type, actor_id = _audit_from_current(current)
        row.updated_by_type = actor_type
        row.updated_by_id = actor_id

        if "password" in payload and payload["password"]:
            row.password_hash = get_password_hash(payload.pop("password"))
        if "role" in payload and payload["role"] is not None:
            row.role = payload.pop("role").value
        if "salary_system" in payload:
            ss = payload.pop("salary_system")
            row.salary_system = ss.value if ss is not None else None
        if "organisation_structure_id" in payload:
            raw_org = payload.pop("organisation_structure_id")
            org_id = str(raw_org) if raw_org is not None else None
            ensure_organisation_structure_for_company(self._db, company_id, org_id)
            row.organisation_structure_id = org_id
        for k, v in payload.items():
            setattr(row, k, v)

        try:
            if new_ids and not row.is_active:
                raise ValueError("Cannot add permissions to an inactive employee.")

            if removed_ids is not None:
                for pid in removed_ids:
                    self._deactivate_permission(employee_id, str(pid), actor_type, actor_id)

            if new_ids is not None:
                for pid in new_ids:
                    self._add_or_reactivate_permission(employee_id, str(pid), actor_type, actor_id)

            if removed_branch_ids is not None:
                for bid in removed_branch_ids:
                    self._unassign_branch(employee_id, str(bid))

            if new_branch_ids is not None:
                if not row.is_active:
                    raise ValueError("Cannot assign branches to an inactive employee.")
                for bid in new_branch_ids:
                    self._assign_branch(employee_id, str(bid), company_id, actor_type, actor_id)

            self._db.flush()
            refresh_organisation_structure_totals(
                self._db,
                previous_org_id,
                row.organisation_structure_id,
            )
            self._repo.save_employee(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update employee.") from e
        except ValueError:
            self._db.rollback()
            raise

        return self._repo.get_employee(employee_id, load_children=True)

    def deactivate_employee(self, company_id: str, employee_id: str, current: CurrentClient) -> bool:
        """Soft-delete: mark deleted, deactivate login and related phones/permissions."""
        ensure_employer_manage_access(self._db, current, company_id)
        row = self._get_for_company(company_id, employee_id, load_children=True)
        if row is None:
            return False
        if row.is_deleted:
            return True
        previous_org_id = row.organisation_structure_id
        actor_type, actor_id = _audit_from_current(current)
        now = utc_now()
        row.is_deleted = True
        row.deleted_at = now
        row.is_active = False
        row.updated_by_type = actor_type
        row.updated_by_id = actor_id
        for p in row.phones:
            p.is_active = False
            p.is_primary = False
            p.updated_by_type = actor_type
            p.updated_by_id = actor_id
        for link in row.app_permissions:
            link.is_active = False
            link.updated_by_type = actor_type
            link.updated_by_id = actor_id
        try:
            self._db.flush()
            refresh_organisation_structure_totals(self._db, previous_org_id)
            self._repo.save_employee(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not delete employee.") from e
        return True

    def add_phone(
        self,
        company_id: str,
        employee_id: str,
        current: CurrentClient,
        data: CompanyEmployeePhoneCreate,
    ) -> CompanyEmployeePhone:
        ensure_employer_manage_access(self._db, current, company_id)
        emp = self._get_for_company(company_id, employee_id, load_children=False)
        if emp is None:
            raise ValueError("Employee not found.")
        if emp.is_deleted:
            raise ValueError("Cannot add phone to a deleted employee.")
        if not emp.is_active:
            raise ValueError("Cannot add phone to an inactive employee.")
        actor_type, actor_id = _audit_from_current(current)
        if data.is_primary:
            self._repo.clear_primary_phones(employee_id, except_phone_id=None)
        phone_row = CompanyEmployeePhone(
            employee_id=employee_id,
            phone_number=data.phone_number,
            is_primary=data.is_primary,
            is_active=True,
            created_by_type=actor_type,
            created_by_id=actor_id,
            updated_by_type=actor_type,
            updated_by_id=actor_id,
        )
        self._db.add(phone_row)
        try:
            self._db.commit()
            self._db.refresh(phone_row)
        except IntegrityError as e:
            self._db.rollback()
            if "ix_company_employee_phones_phone_number" in str(e.orig):
                raise ValueError("This phone number is already registered.") from e
            if "uq_company_employee_phones_one_primary_active" in str(e.orig):
                raise ValueError("Only one primary active phone is allowed per employee.") from e
            raise ValueError("Could not add phone.") from e
        return phone_row

    def update_phone(
        self,
        company_id: str,
        employee_id: str,
        phone_id: str,
        current: CurrentClient,
        data: CompanyEmployeePhoneUpdate,
    ) -> CompanyEmployeePhone | None:
        ensure_employer_manage_access(self._db, current, company_id)
        if self._get_for_company(company_id, employee_id, load_children=False) is None:
            return None
        row = self._repo.get_phone(phone_id)
        if row is None or row.employee_id != employee_id:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        if payload.get("is_active") is False:
            payload["is_primary"] = False
        if payload.get("is_primary") is True:
            self._repo.clear_primary_phones(employee_id, except_phone_id=phone_id)
        actor_type, actor_id = _audit_from_current(current)
        row.updated_by_type = actor_type
        row.updated_by_id = actor_id
        if "phone_number" in payload and payload["phone_number"] is not None:
            row.phone_number = payload.pop("phone_number")
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            return self._repo.save_phone(row)
        except IntegrityError as e:
            self._db.rollback()
            if "ix_company_employee_phones_phone_number" in str(e.orig):
                raise ValueError("This phone number is already registered.") from e
            if "uq_company_employee_phones_one_primary_active" in str(e.orig):
                raise ValueError("Only one primary active phone is allowed per employee.") from e
            raise ValueError("Could not update phone.") from e

    def deactivate_phone(
        self,
        company_id: str,
        employee_id: str,
        phone_id: str,
        current: CurrentClient,
    ) -> bool:
        ensure_employer_manage_access(self._db, current, company_id)
        if self._get_for_company(company_id, employee_id, load_children=False) is None:
            return False
        row = self._repo.get_phone(phone_id)
        if row is None or row.employee_id != employee_id:
            return False
        actor_type, actor_id = _audit_from_current(current)
        row.is_active = False
        row.is_primary = False
        row.updated_by_type = actor_type
        row.updated_by_id = actor_id
        try:
            self._repo.save_phone(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not deactivate phone.") from e
        return True

    def list_employee_app_permissions(
        self,
        company_id: str,
        employee_id: str,
        current: CurrentClient,
        *,
        active_only: bool = False,
    ) -> list[EmployeeAppPermission] | None:
        ensure_employer_manage_access(self._db, current, company_id)
        emp = self._get_for_company(company_id, employee_id, load_children=True)
        if emp is None:
            return None
        links = list(emp.app_permissions)
        if active_only:
            links = [x for x in links if x.is_active]
        return links

    def list_employees_beasy(
        self,
        *,
        company_id: str | None,
        role: str | None,
        department: str | None,
        is_active: bool | None,
    ) -> list[CompanyEmployee]:
        return self._repo.list_filtered(
            company_id=company_id,
            role=role,
            department=department,
            is_active=is_active,
        )

    def get_employee_beasy(self, employee_id: str) -> CompanyEmployee | None:
        return self._repo.get_employee(employee_id, load_children=True)
