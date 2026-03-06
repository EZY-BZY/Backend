"""
Create initial admin user for a company.
Usage: python -m scripts.create_admin <company_slug> <email> <password>
Example: python -m scripts.create_admin acme admin@acme.com SecurePass123
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.modules.companies.models import Company
from app.modules.roles.models import Role
from app.modules.users.models import User, UserRole
from sqlalchemy import select


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python -m scripts.create_admin <company_slug> <email> <password>")
        sys.exit(1)
    company_slug, email, password = sys.argv[1], sys.argv[2], sys.argv[3]

    db = SessionLocal()
    try:
        company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
        if not company:
            print(f"Company with slug '{company_slug}' not found. Create the company first.")
            sys.exit(1)
        existing = db.execute(
            select(User).where(User.company_id == company.id, User.email == email)
        ).scalar_one_or_none()
        if existing:
            print(f"User {email} already exists in company {company_slug}.")
            sys.exit(0)
        admin_role = db.execute(
            select(Role).where(Role.company_id == company.id, Role.name == "admin")
        ).scalar_one_or_none()
        if not admin_role:
            admin_role = db.execute(
                select(Role).where(Role.company_id == company.id, Role.name == "owner")
            ).scalar_one_or_none()
        if not admin_role:
            print("No 'admin' or 'owner' role found. Run seed_roles_permissions first.")
            sys.exit(1)
        user = User(
            company_id=company.id,
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Admin",
            is_active=True,
            is_blocked=False,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))
        db.commit()
        print(f"Created admin user {email} for company {company_slug} with role {admin_role.name}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
