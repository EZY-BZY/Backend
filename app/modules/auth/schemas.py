"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login with email and password. Company context via header or first company."""

    email: EmailStr
    password: str = Field(..., min_length=1)
    company_slug: str | None = Field(None, description="Company to log into (slug)")


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str
