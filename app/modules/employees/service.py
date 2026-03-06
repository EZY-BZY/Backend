"""Business logic for employees: owner creation (once) and members CRUD."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.employees.enums import AccountType
from app.modules.employees.models import Employee, EmployeePermission
from app.modules.employees.repository import EmployeePermissionRepository, EmployeeRepository
from app.modules.employees.schemas import MemberCreate, MemberUpdate, OwnerCreate


class EmployeeService:
    """Public API for employees (owner + members)."""

    def __init__(self, db: Session) -> None:
        self._repo = EmployeeRepository(db)
        self._perm_repo = EmployeePermissionRepository(db)

    def owner_exists(self) -> bool:
        """Return True if organization owner already exists. Enforced at service + DB."""
        return self._repo.owner_exists()

    def create_owner(self, data: OwnerCreate, created_by_id: UUID | str | None = None) -> Employee:
        """
        Create organization owner. Fails if owner already exists.
        Only one owner allowed in the whole system.
        """
        if self._repo.owner_exists():
            raise ValueError("Organization owner already exists. Only one owner is allowed.")
        employee = Employee(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=get_password_hash(data.password),
            account_type=AccountType.OWNER.value,
            account_status="active",
            created_by_id=str(created_by_id) if created_by_id else None,
            updated_by_id=str(created_by_id) if created_by_id else None,
        )
        return self._repo.create(employee)

    def get_by_id(self, employee_id: UUID | str, include_deleted: bool = False) -> Employee | None:
        """Get employee by id. By default excludes soft-deleted."""
        if include_deleted:
            return self._repo.get_by_id(employee_id)
        return self._repo.get_by_id_excluding_deleted(employee_id)

    def get_by_email(self, email: str) -> Employee | None:
        return self._repo.get_by_email(email)

    def create_member(
        self,
        data: MemberCreate,
        created_by_id: UUID | str | None,
    ) -> Employee:
        """Create a member (non-owner). Owner cannot be created through this."""
        if data.account_type == AccountType.OWNER:
            raise ValueError("Use create_owner to create the organization owner.")
        if self._repo.get_by_email(data.email):
            raise ValueError("An employee with this email already exists.")
        employee = Employee(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=get_password_hash(data.password),
            account_type=data.account_type.value,
            account_status=data.account_status.value,
            created_by_id=str(created_by_id) if created_by_id else None,
            updated_by_id=str(created_by_id) if created_by_id else None,
        )
        created = self._repo.create(employee)
        if data.permission_names:
            self._perm_repo.set_permissions(
                created.id, data.permission_names, created_by_id=created_by_id
            )
        return created

    def update_member(
        self,
        employee_id: UUID | str,
        data: MemberUpdate,
        updated_by_id: UUID | str | None,
    ) -> Employee | None:
        """Update member. Cannot change account_type to owner here."""
        employee = self._repo.get_by_id_excluding_deleted(employee_id)
        if not employee:
            return None
        if employee.account_type == AccountType.OWNER.value:
            raise ValueError("Cannot update owner through members API.")
        update_data = data.model_dump(exclude_unset=True)
        if "account_type" in update_data and update_data["account_type"] == AccountType.OWNER:
            raise ValueError("Cannot set account_type to owner.")
        if "permission_names" in update_data:
            perm_names = update_data.pop("permission_names")
            self._perm_repo.set_permissions(employee_id, perm_names, created_by_id=updated_by_id)
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
    ) -> tuple[list[Employee], int]:
        """List members only (owner always excluded). Paginated. Newest first."""
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
    ) -> Employee | None:
        """Soft-delete member: set deleted_at. Owner cannot be deactivated through this."""
        employee = self._repo.get_by_id_excluding_deleted(employee_id)
        if not employee:
            return None
        if employee.account_type == AccountType.OWNER.value:
            raise ValueError("Cannot deactivate the organization owner.")
        from datetime import datetime, timezone

        employee.deleted_at = datetime.now(timezone.utc)
        employee.updated_by_id = str(updated_by_id) if updated_by_id else None
        return self._repo.update(employee)

    def get_permission_names(self, employee_id: UUID | str) -> list[str]:
        """Get permission names for employee from DB. Used by require_permission."""
        return self._repo.get_permission_names(employee_id)

    def employee_has_permission(self, employee_id: UUID | str, permission_name: str) -> bool:
        """Check if employee has the given permission (from DB)."""
        return permission_name in self.get_permission_names(employee_id)
