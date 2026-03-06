"""User (employee) Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Create user (employee) within a company."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Partial user update."""

    full_name: str | None = None
    is_active: bool | None = None
    is_blocked: bool | None = None


class UserRead(UserBase):
    """User response (no password)."""

    id: UUID
    company_id: UUID
    is_active: bool
    is_blocked: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UserReadWithRoles(UserRead):
    """User with role names (for admin views)."""

    role_names: list[str] = []
