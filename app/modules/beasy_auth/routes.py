"""Beasy dashboard auth: login and token refresh for Beasy employees."""

from fastapi import APIRouter, HTTPException

from app.common.api_response import ApiResponse
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.session import DbSession
from app.modules.beasy_auth.schemas import DashboardLoginRequest, RefreshTokenRequest
from app.modules.beasy_employees.schemas import TokenResponse
from app.modules.beasy_employees.service import EmployeeService

router = APIRouter(prefix="/auth", tags=["Authentication (Beasy)"])


def _employee_service(db: DbSession) -> EmployeeService:
    return EmployeeService(db)


@router.post("/login", response_model=ApiResponse[TokenResponse])
def dashboard_login(data: DashboardLoginRequest, db: DbSession):
    """
    Log into the Beasy dashboard. Validates a Beasy employee by email/password and returns
    access + refresh JWTs (`sub` = employee id). Use `Authorization: Bearer <access_token>`
    on protected Beasy routes.
    """
    service = _employee_service(db)
    employee = service.get_by_email(str(data.email))
    if not employee or not verify_password(data.password, employee.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if employee.account_status != "active":
        raise HTTPException(status_code=403, detail="Account is inactive or suspended")
    if employee.deleted_at:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    settings = get_settings()
    access = create_access_token(employee.id)
    refresh = create_refresh_token(employee.id)
    return ApiResponse(
        status_code=200,
        Message="Login successful",
        Data=TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh_tokens(body: RefreshTokenRequest, db: DbSession):
    """Exchange a valid refresh JWT for a new access + refresh pair."""
    payload = decode_token(body.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    service = _employee_service(db)
    employee = service.get_by_id(sub, include_deleted=False)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid or inactive user")
    if employee.account_status != "active" or employee.deleted_at:
        raise HTTPException(status_code=401, detail="Invalid or inactive user")

    settings = get_settings()
    access = create_access_token(employee.id)
    refresh = create_refresh_token(employee.id)
    return ApiResponse(
        status_code=200,
        Message="Tokens refreshed",
        Data=TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )
