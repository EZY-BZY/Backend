"""Role and Permission repository. Internal to roles module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.models import Permission, Role, RolePermission


class RoleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_role_by_id(self, role_id: UUID | str) -> Role | None:
        return self.db.get(Role, str(role_id))

    def get_role_by_company_and_name(self, company_id: UUID | str, name: str) -> Role | None:
        stmt = select(Role).where(
            Role.company_id == str(company_id),
            Role.name == name,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_roles_by_company(self, company_id: UUID | str) -> list[Role]:
        stmt = select(Role).where(Role.company_id == str(company_id))
        return list(self.db.execute(stmt).scalars().all())

    def create_role(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role


class PermissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_code(self, code: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create_by_code(self, code: str, name: str, description: str | None = None) -> Permission:
        p = self.get_by_code(code)
        if p:
            return p
        p = Permission(code=code, name=name, description=description)
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def list_all(self) -> list[Permission]:
        stmt = select(Permission)
        return list(self.db.execute(stmt).scalars().all())
