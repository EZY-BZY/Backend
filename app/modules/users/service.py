"""User service - business logic. Public API of users module."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    """Public service for user (employee) operations."""

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)

    def get_by_id(self, user_id: UUID | str) -> User | None:
        """Get user by id."""
        return self._repo.get_by_id(user_id)

    def get_by_id_and_company(self, user_id: UUID | str, company_id: UUID | str) -> User | None:
        """Get user by id within company (tenant isolation)."""
        return self._repo.get_by_id_and_company(user_id, company_id)

    def get_by_email_and_company(self, email: str, company_id: UUID | str) -> User | None:
        """Get user by email within company (for login)."""
        return self._repo.get_by_email_and_company(email, company_id)

    def create(self, company_id: UUID | str, data: UserCreate) -> User:
        """Create user (employee) in company."""
        user = User(
            company_id=str(company_id),
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            is_active=True,
            is_blocked=False,
        )
        return self._repo.create(user)

    def update(self, user_id: UUID | str, company_id: UUID | str, data: UserUpdate) -> User | None:
        """Update user; enforces company scope."""
        user = self._repo.get_by_id_and_company(user_id, company_id)
        if not user:
            return None
        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(user, k, v)
        return self._repo.update(user)

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[User]:
        """List users in company (tenant-scoped)."""
        return self._repo.list_by_company(company_id, skip=skip, limit=limit, active_only=active_only)
