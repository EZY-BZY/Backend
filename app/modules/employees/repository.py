"""Data access for employees and permissions."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.employees.enums import AccountType
from app.modules.employees.models import Employee, EmployeePermission


class EmployeeRepository:
    """Repository for Employee and EmployeePermission."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, employee_id: UUID | str) -> Employee | None:
        """Get employee by id. Includes soft-deleted unless excluded."""
        return self.db.get(Employee, str(employee_id))

    def get_by_id_excluding_deleted(self, employee_id: UUID | str) -> Employee | None:
        """Get employee by id; None if soft-deleted."""
        emp = self.db.get(Employee, str(employee_id))
        if emp and emp.deleted_at is None:
            return emp
        return None

    def get_by_email(self, email: str, exclude_deleted: bool = True) -> Employee | None:
        """Get employee by email."""
        stmt = select(Employee).where(Employee.email == email)
        if exclude_deleted:
            stmt = stmt.where(Employee.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def owner_exists(self) -> bool:
        """Return True if an owner already exists (any status)."""
        stmt = select(func.count()).select_from(Employee).where(
            Employee.account_type == AccountType.OWNER.value,
            Employee.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one() > 0

    def create(self, employee: Employee) -> Employee:
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def update(self, employee: Employee) -> Employee:
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def list_members(
        self,
        *,
        account_status: str | None = None,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Employee], int]:
        """
        List members only (owner excluded). Excludes soft-deleted.
        Returns (items, total_count).
        """
        base = (
            select(Employee)
            .where(Employee.account_type != AccountType.OWNER.value)
            .where(Employee.deleted_at.is_(None))
        )
        if account_status:
            base = base.where(Employee.account_status == account_status)
        if name:
            base = base.where(Employee.full_name.ilike(f"%{name}%"))
        if email:
            base = base.where(Employee.email.ilike(f"%{email}%"))
        if phone:
            base = base.where(Employee.phone.ilike(f"%{phone}%"))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = base.order_by(Employee.created_at.desc()).offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def get_permission_names(self, employee_id: UUID | str) -> list[str]:
        """Get list of permission names for an employee from DB."""
        stmt = (
            select(EmployeePermission.permission_name)
            .where(EmployeePermission.employee_id == str(employee_id))
        )
        return [row[0] for row in self.db.execute(stmt).all()]


class EmployeePermissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def set_permissions(
        self,
        employee_id: UUID | str,
        permission_names: list[str],
        created_by_id: UUID | str | None = None,
    ) -> None:
        """Replace all permissions for employee with the given list."""
        existing = self.db.execute(
            select(EmployeePermission).where(EmployeePermission.employee_id == str(employee_id))
        ).scalars().all()
        for ep in existing:
            self.db.delete(ep)
        self.db.flush()
        for name in permission_names:
            if not name.strip():
                continue
            ep = EmployeePermission(
                employee_id=str(employee_id),
                permission_name=name.strip(),
                created_by_id=str(created_by_id) if created_by_id else None,
            )
            self.db.add(ep)
        self.db.commit()
