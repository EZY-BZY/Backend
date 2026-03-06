"""Auth dependencies: get_current_user, get_current_company_member, require_permission."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import DbSession
from app.modules.users.models import User
from app.modules.users.service import UserService

# OAuth2PasswordBearer for optional auth on some routes; HTTPBearer for required Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def _get_token_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict | None:
    """Extract and decode JWT from Bearer token."""
    if not credentials:
        return None
    return decode_token(credentials.credentials)


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> User | None:
    """
    Resolve current user from JWT. Returns None if no/invalid token.
    Use get_current_active_user when you require a logged-in user.
    """
    payload = _get_token_payload(credentials)
    if not payload or payload.get("type") != "access":
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    user_svc = UserService(db)
    return user_svc.get_by_id(sub)


def get_current_user_required(
    current_user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """Require authenticated user; raise 401 if not."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user_required)],
) -> User:
    """Require active, non-blocked user."""
    if not current_user.is_active or current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive or blocked",
        )
    return current_user


def get_current_company_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> str | None:
    """Extract company_id from JWT (tenant context). Never trust client-sent company_id."""
    payload = _get_token_payload(credentials)
    if not payload:
        return None
    return payload.get("company_id")


def get_current_company_member(
    current_user: Annotated[User, Depends(get_current_active_user)],
    company_id_from_token: Annotated[str | None, Depends(get_current_company_id)],
) -> User:
    """
    Require current user and ensure they belong to the company in the token.
    Use this for tenant-scoped routes; never use client-provided company_id for filtering.
    """
    if not company_id_from_token or str(current_user.company_id) != company_id_from_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company context invalid or access denied",
        )
    return current_user


def require_permission(permission_code: str):
    """
    Factory: returns a dependency that requires the given permission.
    Usage: Depends(require_permission("orders:manage"))
    """

    def _require(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: DbSession,
    ) -> User:
        from app.modules.roles.service import RoleService
        role_svc = RoleService(db)
        if not role_svc.user_has_permission(current_user.id, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_code}",
            )
        return current_user

    return _require


# Type aliases for route injection
CurrentUser = Annotated[User | None, Depends(get_current_user)]
CurrentUserRequired = Annotated[User, Depends(get_current_active_user)]
CurrentCompanyMember = Annotated[User, Depends(get_current_company_member)]
