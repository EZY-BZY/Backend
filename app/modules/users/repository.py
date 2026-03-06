"""User repository - data access. Internal to users module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import User, UserRole


class UserRepository:
    """Data access for users."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: UUID | str) -> User | None:
        """Get user by id."""
        return self.db.get(User, str(user_id))

    def get_by_id_and_company(self, user_id: UUID | str, company_id: UUID | str) -> User | None:
        """Get user by id ensuring they belong to company (tenant isolation)."""
        user = self.db.get(User, str(user_id))
        if user and str(user.company_id) == str(company_id):
            return user
        return None

    def get_by_email_and_company(self, email: str, company_id: UUID | str) -> User | None:
        """Get user by email within a company."""
        stmt = select(User).where(
            User.email == email,
            User.company_id == str(company_id),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        """Persist user."""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Commit user changes."""
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[User]:
        """List users for a company (tenant-scoped)."""
        stmt = select(User).where(User.company_id == str(company_id))
        if active_only:
            stmt = stmt.where(User.is_active.is_(True), User.is_blocked.is_(False))
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
