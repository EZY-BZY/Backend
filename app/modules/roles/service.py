"""Role service - business logic. Public API of roles module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.models import Permission, Role, RolePermission
from app.modules.users.models import UserRole
from app.modules.roles.repository import PermissionRepository, RoleRepository


class RoleService:
    """Public service for roles and permissions."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._role_repo = RoleRepository(db)
        self._perm_repo = PermissionRepository(db)

    def get_role_by_id(self, role_id: UUID | str) -> Role | None:
        return self._role_repo.get_role_by_id(role_id)

    def get_role_by_company_and_name(self, company_id: UUID | str, name: str) -> Role | None:
        return self._role_repo.get_role_by_company_and_name(company_id, name)

    def list_roles_by_company(self, company_id: UUID | str) -> list[Role]:
        return self._role_repo.list_roles_by_company(company_id)

    def get_permission_codes_for_user(self, user_id: UUID | str) -> set[str]:
        """
        Resolve all permission codes for a user (via user_roles -> role -> role_permissions -> permission).
        Public API for auth module to perform permission checks.
        """
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == str(user_id))
        )
        result = self._db.execute(stmt)
        return {row[0] for row in result.all()}

    def user_has_permission(self, user_id: UUID | str, permission_code: str) -> bool:
        """Check if user has the given permission."""
        return permission_code in self.get_permission_codes_for_user(user_id)

    def get_or_create_permission(self, code: str, name: str, description: str | None = None) -> Permission:
        return self._perm_repo.get_or_create_by_code(code, name, description)

    def list_permissions(self) -> list[Permission]:
        return self._perm_repo.list_all()
