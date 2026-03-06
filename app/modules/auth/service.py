"""Auth service - login, token creation. Public API of auth module."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.modules.companies.service import CompanyService
from app.modules.users.models import User
from app.modules.users.service import UserService


class AuthService:
    """Handles login and token issuance."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._user_svc = UserService(db)
        self._company_svc = CompanyService(db)

    def authenticate(
        self, email: str, password: str, company_slug: str | None = None
    ) -> tuple[User, str] | None:
        """
        Authenticate user by email/password. If company_slug given, restrict to that company.
        Returns (user, company_id) or None.
        """
        # Resolve company: by slug or first company (simplified for boilerplate)
        company_id: str | None = None
        if company_slug:
            company = self._company_svc.get_by_slug(company_slug)
            if not company:
                return None
            company_id = company.id
        # Find user: must be within a company
        if company_id:
            user = self._user_svc.get_by_email_and_company(email, company_id)
        else:
            from sqlalchemy import select
            stmt = select(User).where(User.email == email).limit(1)
            user = self._db.execute(stmt).scalar_one_or_none()
            if user:
                company_id = user.company_id
            else:
                return None

        if not user or not company_id:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active or user.is_blocked:
            return None
        return (user, company_id)

    def create_tokens(self, user_id: UUID | str, company_id: UUID | str) -> dict:
        """Create access and refresh tokens for user in company context."""
        settings = get_settings()
        access = create_access_token(user_id, company_id=company_id)
        refresh = create_refresh_token(user_id)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    def refresh_access_token(self, refresh_token: str) -> dict | None:
        """Validate refresh token and return new token pair or None."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        sub = payload.get("sub")
        if not sub:
            return None
        user = self._user_svc.get_by_id(sub)
        if not user or not user.is_active or user.is_blocked:
            return None
        # Re-issue with user's company (from token or default to user's company)
        company_id = payload.get("company_id") or user.company_id
        return self.create_tokens(user.id, company_id)
