"""Pydantic schemas for Beasy employees (`beasy_employees`)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.common.allenums import AccountStatus, AccountType


class TokenResponse(BaseModel):
    """JWT access + refresh pair (organization login)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class BEasyEmployeeBase(BaseModel):
    """Shared fields for employee."""

    name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    phone: str | None = Field(None, max_length=64)
    account_type: AccountType = AccountType.MEMBER
    account_status: AccountStatus = AccountStatus.ACTIVE


class BEasySuperUserCreate(BaseModel):
    """Create B-easy Super User. Only one allowed in the system."""

    name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    phone: str | None = Field(None, max_length=64)
    password: str = Field(..., min_length=8)


class BEasyMemberCreate(BaseModel):
    """Create member (non-Super User employee)."""

    name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    phone: str | None = Field(None, max_length=64)
    password: str = Field(..., min_length=8)
    account_type: AccountType = Field(default=AccountType.MEMBER)
    account_status: AccountStatus = Field(default=AccountStatus.ACTIVE)


class BEasyMemberUpdate(BaseModel):
    """Partial update for member."""

    name: str | None = Field(None, min_length=1, max_length=256)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=64)
    account_type: AccountType | None = None
    account_status: AccountStatus | None = None


class BEasyEmployeeRead(BaseModel):
    """Employee response (no password). Super User excluded from members list."""

    id: UUID
    name: str
    email: str
    phone: str | None
    account_type: str
    account_status: str
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID | None
    updated_by_id: UUID | None

    model_config = {"from_attributes": True}



class BEasyMemberListFilters(BaseModel):
    """Query params for list members."""

    account_status: AccountStatus | None = None
    name: str | None = Field(None, max_length=256, description="Search in name")
    email: str | None = Field(None, max_length=256)
    phone: str | None = Field(None, max_length=64)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class BEasyLoginRequest(BaseModel):
    """Login request: email + password. Returns JWT with employee_id as sub."""

    email: EmailStr
    password: str = Field(..., min_length=1)


# Backwards-compatible names for routes
EmployeeRead = BEasyEmployeeRead
MemberCreate = BEasyMemberCreate
MemberUpdate = BEasyMemberUpdate
OwnerCreate = BEasySuperUserCreate
OrgLoginRequest = BEasyLoginRequest
