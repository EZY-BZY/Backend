"""Business logic for B-easy employees: Super User (once) and members CRUD."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.common.allenums import AccountType, AccountStatus
from app.modules.beasy_employees.models import BEasyEmployee
from app.modules.beasy_employees.repository import BEasyEmployeeRepository
from app.modules.beasy_employees.schemas import BEasyMemberCreate, BEasyMemberUpdate, BEasySuperUserCreate


class EmployeeService:
    """Public API for B-easy employees (Super User + members)."""

    def __init__(self, db: Session) -> None:
        self._repo = BEasyEmployeeRepository(db)

    def super_user_exists(self) -> bool:
        """Return True if B-easy Super User already exists. Enforced at service + DB."""
        return self._repo.super_user_exists()

    def create_super_user(self, data: BEasySuperUserCreate, created_by_id: UUID | str | None = None) -> BEasyEmployee:
        """
        Create B-easy Super User. Fails if Super User already exists.
        Only one Super User allowed in the whole system.
        """
        if self._repo.super_user_exists():
            raise ValueError("B-easy Super User already exists. Only one Super User is allowed.")
        employee = BEasyEmployee(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password_hash=get_password_hash(data.password),
            account_type=AccountType.SUPER_USER.value,
            account_status=AccountStatus.ACTIVE.value,
            created_by_id=str(created_by_id) if created_by_id else None,
            updated_by_id=str(created_by_id) if created_by_id else None,
        )
        return self._repo.create(employee)

    def get_by_id(self, employee_id: UUID | str, include_deleted: bool = False) -> BEasyEmployee | None:
        """Get B-easy employee by id. By default excludes soft-deleted."""
        if include_deleted:
            return self._repo.get_by_id(employee_id)
        return self._repo.get_by_id_excluding_deleted(employee_id)

    def get_by_email(self, email: str) -> BEasyEmployee | None:
        return self._repo.get_by_email(email)

    def get_by_phone(self, phone: str) -> BEasyEmployee | None:
        return self._repo.get_by_phone(phone)

    def create_member(
        self,
        data: BEasyMemberCreate,
        created_by_id: UUID | str | None,
    ) -> BEasyEmployee:
        """Create a member (non–Super User). Super User cannot be created through this."""
        if data.account_type == AccountType.SUPER_USER:
            raise ValueError("Use create_super_user to create the B-easy Super User.")
        if self._repo.get_by_email(data.email):
            raise ValueError("An employee with this email already exists.")
        employee = BEasyEmployee(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password_hash=get_password_hash(data.password),
            account_type=data.account_type.value,
            account_status=data.account_status.value,
            created_by_id=str(created_by_id) if created_by_id else None,
            updated_by_id=str(created_by_id) if created_by_id else None,
        )
        return self._repo.create(employee)

    def update_member(
        self,
        employee_id: UUID | str,
        data: BEasyMemberUpdate,
        updated_by_id: UUID | str | None,
    ) -> BEasyEmployee | None:
        """Update member. Cannot change account_type to Super User here."""
        employee = self._repo.get_by_id_excluding_deleted(employee_id)
        if not employee:
            return None
        if employee.account_type == AccountType.SUPER_USER.value:
            raise ValueError("Cannot update Super User through members API.")
        update_data = data.model_dump(exclude_unset=True)
        if "account_type" in update_data and update_data["account_type"] == AccountType.SUPER_USER:
            raise ValueError("Cannot set account_type to Super User.")
        for key, value in update_data.items():
            if key == "account_type" and value is not None:
                setattr(employee, key, value.value)
            elif key == "account_status" and value is not None:
                setattr(employee, key, value.value)
            elif value is not None:
                setattr(employee, key, value)
        employee.updated_by_id = str(updated_by_id) if updated_by_id else None
        return self._repo.update(employee)

    def list_members(
        self,
        *,
        account_status: str | None = None,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BEasyEmployee], int]:
        """List members only (Super User always excluded). Paginated. Newest first."""
        skip = (page - 1) * page_size
        return self._repo.list_members(
            account_status=account_status,
            name=name,
            email=email,
            phone=phone,
            skip=skip,
            limit=page_size,
        )

    def deactivate_member(
        self, employee_id: UUID | str, updated_by_id: UUID | str | None
    ) -> BEasyEmployee | None:
        """Soft-delete member: set deleted_at. Super User cannot be deactivated through this."""
        employee = self._repo.get_by_id_excluding_deleted(employee_id)
        if not employee:
            return None
        if employee.account_type == AccountType.SUPER_USER.value:
            raise ValueError("Cannot deactivate the B-easy Super User.")
        from datetime import datetime, timezone

        employee.deleted_at = datetime.now(timezone.utc)
        employee.updated_by_id = str(updated_by_id) if updated_by_id else None
        return self._repo.update(employee)
