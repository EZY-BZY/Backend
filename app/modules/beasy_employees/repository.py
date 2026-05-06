"""Data access for B-easy employees."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.allenums import AccountType
from app.modules.beasy_employees.models import BEasyEmployee


class BEasyEmployeeRepository:
    """Repository for BEasyEmployee."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, employee_id: UUID | str) -> BEasyEmployee | None:
        """Get employee by id. Includes soft-deleted unless excluded."""
        return self.db.get(BEasyEmployee, str(employee_id))

    def get_by_id_excluding_deleted(self, employee_id: UUID | str) -> BEasyEmployee | None:
        """Get employee by id; None if soft-deleted."""
        emp = self.db.get(BEasyEmployee, str(employee_id))
        if emp and emp.deleted_at is None:
            return emp
        return None

    def get_by_email(self, email: str, exclude_deleted: bool = True) -> BEasyEmployee | None:
        """Get employee by email."""
        stmt = select(BEasyEmployee).where(BEasyEmployee.email == email)
        if exclude_deleted:
            stmt = stmt.where(BEasyEmployee.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_phone(self, phone: str, exclude_deleted: bool = True) -> BEasyEmployee | None:
        """Get employee by phone."""
        stmt = select(BEasyEmployee).where(BEasyEmployee.phone == phone)
        if exclude_deleted:
            stmt = stmt.where(BEasyEmployee.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def super_user_exists(self) -> bool:
        """Return True if a Super User already exists (not soft-deleted)."""
        stmt = select(func.count()).select_from(BEasyEmployee).where(
            BEasyEmployee.account_type == AccountType.SUPER_USER.value,
            BEasyEmployee.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one() > 0

    def create(self, employee: BEasyEmployee) -> BEasyEmployee:
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def update(self, employee: BEasyEmployee) -> BEasyEmployee:
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
    ) -> tuple[list[BEasyEmployee], int]:
        """
        List members only (Super User excluded). Excludes soft-deleted.
        Returns (items, total_count).
        """
        base = (
            select(BEasyEmployee)
            .where(BEasyEmployee.account_type != AccountType.SUPER_USER.value)
            .where(BEasyEmployee.deleted_at.is_(None))
        )
        if account_status:
            base = base.where(BEasyEmployee.account_status == account_status)
        if name:
            base = base.where(BEasyEmployee.name.ilike(f"%{name}%"))
        if email:
            base = base.where(BEasyEmployee.email.ilike(f"%{email}%"))
        if phone:
            base = base.where(BEasyEmployee.phone.ilike(f"%{phone}%"))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = base.order_by(BEasyEmployee.created_at.desc()).offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total
