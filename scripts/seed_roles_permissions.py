"""
Seed default roles and permissions.
Run from project root: python -m scripts.seed_roles_permissions
Requires DB to be migrated and DATABASE_URL set.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
import app.db.models_registry  # noqa: F401
from app.modules.companies.models import Company
from app.modules.roles.models import Role, Permission, RolePermission
from app.modules.roles.constants import (
    DEFAULT_ROLES,
    DEFAULT_PERMISSIONS,
    ROLE_PERMISSIONS,
)


def seed_permissions(session: Session) -> dict[str, str]:
    """Create permissions by code; return code -> id map."""
    code_to_id = {}
    for code in DEFAULT_PERMISSIONS:
        name = code.replace(":", " ").title()
        existing = session.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
        if existing:
            code_to_id[code] = existing.id
        else:
            p = Permission(code=code, name=name, description=f"Permission: {code}")
            session.add(p)
            session.flush()
            code_to_id[code] = p.id
    return code_to_id


def seed_company_roles(session: Session, company_id: str, code_to_id: dict[str, str]) -> None:
    """Create default roles for a company and assign permissions."""
    for role_name in DEFAULT_ROLES:
        existing = session.execute(
            select(Role).where(
                Role.company_id == company_id,
                Role.name == role_name,
            )
        ).scalar_one_or_none()
        if existing:
            role_id = existing.id
        else:
            role = Role(company_id=company_id, name=role_name, description=f"Role: {role_name}")
            session.add(role)
            session.flush()
            role_id = role.id

        perm_codes = ROLE_PERMISSIONS.get(role_name, [])
        for code in perm_codes:
            perm_id = code_to_id.get(code)
            if not perm_id:
                continue
            exists = session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == perm_id,
                )
            ).scalar_one_or_none()
            if not exists:
                session.add(RolePermission(role_id=role_id, permission_id=perm_id))


def main() -> None:
    settings = get_settings()
    url = settings.database_url.unicode_string()
    engine = create_engine(url)
    with Session(engine) as session:
        code_to_id = seed_permissions(session)
        session.flush()
        companies = session.execute(select(Company)).scalars().all()
        for company in companies:
            seed_company_roles(session, company.id, code_to_id)
        session.commit()
    print("Seeded permissions and company roles.")


if __name__ == "__main__":
    main()
