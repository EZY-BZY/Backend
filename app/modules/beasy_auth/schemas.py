"""Request/response models for Beasy dashboard auth."""

from pydantic import BaseModel, EmailStr, Field


class DashboardLoginRequest(BaseModel):
    """Dashboard login: email + password (Beasy employee)."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Exchange a refresh JWT for a new access + refresh pair."""

    refresh_token: str = Field(..., min_length=1)
