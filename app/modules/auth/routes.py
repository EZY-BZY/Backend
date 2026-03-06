"""Auth routes: login, refresh."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_active_user, CurrentUserRequired
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.db.session import DbSession
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """Login with email and password. Optionally pass company_slug to scope to a tenant."""
    service = AuthService(db)
    result = service.authenticate(data.email, data.password, data.company_slug)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials or company")
    user, company_id = result
    tokens = service.create_tokens(user.id, company_id)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DbSession) -> TokenResponse:
    """Exchange refresh token for new access and refresh tokens."""
    service = AuthService(db)
    tokens = service.refresh_access_token(body.refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return TokenResponse(**tokens)


@router.get("/me")
def me(current_user: CurrentUserRequired):
    """Return current user info (for testing auth)."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "company_id": str(current_user.company_id),
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }
