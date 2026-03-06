"""Pydantic schemas for employees (owner + members)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.modules.employees.enums import AccountStatus, AccountType


class EmployeeBase(BaseModel):
    """Shared fields for employee."""

    full_name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    phone: str | None = Field(None, max_length=64)
    account_type: AccountType = AccountType.MEMBER
    account_status: AccountStatus = AccountStatus.ACTIVE


class OwnerCreate(BaseModel):
    """Create organization owner. Only one allowed in the system."""

    full_name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    phone: str | None = Field(None, max_length=64)
    password: str = Field(..., min_length=8)


class MemberCreate(BaseModel):
    """Create member (non-owner employee)."""

    full_name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    phone: str | None = Field(None, max_length=64)
    password: str = Field(..., min_length=8)
    account_type: AccountType = Field(default=AccountType.MEMBER)
    account_status: AccountStatus = Field(default=AccountStatus.ACTIVE)
    permission_names: list[str] = Field(default_factory=list, max_length=50)


class MemberUpdate(BaseModel):
    """Partial update for member."""

    full_name: str | None = Field(None, min_length=1, max_length=256)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=64)
    account_type: AccountType | None = None
    account_status: AccountStatus | None = None
    permission_names: list[str] | None = None


class EmployeeRead(BaseModel):
    """Employee response (no password). Owner excluded from members list."""

    id: UUID
    full_name: str
    email: str
    phone: str | None
    account_type: str
    account_status: str
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID | None
    updated_by_id: UUID | None

    model_config = {"from_attributes": True}


class EmployeeReadWithPermissions(EmployeeRead):
    """Employee with list of permission names."""

    permission_names: list[str] = []


class MemberListFilters(BaseModel):
    """Query params for list members."""

    account_status: AccountStatus | None = None
    name: str | None = Field(None, max_length=256, description="Search in full_name")
    email: str | None = Field(None, max_length=256)
    phone: str | None = Field(None, max_length=64)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class OrgLoginRequest(BaseModel):
    """Organization login: email + password. Returns JWT with employee_id as sub."""

    email: EmailStr
    password: str = Field(..., min_length=1)
