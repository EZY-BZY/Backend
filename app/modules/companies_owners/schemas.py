"""Pydantic schemas for company owners."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.common.allenums import OwnerAccountStatus


class OwnerCheckPhoneResponse(BaseModel):
    registered: bool


class OwnerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    phone: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6)
    email: EmailStr | None = None

    @field_validator("name", "phone", mode="before")
    @classmethod
    def _strip_required(cls, v: str) -> str:
        return str(v).strip()


class OwnerVerifyPhoneRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=64)
    otp: str = Field(..., min_length=1, max_length=32)

    @field_validator("phone", "otp", mode="before")
    @classmethod
    def _strip_required(cls, v: str) -> str:
        return str(v).strip()


class OwnerStatusUpdateRequest(BaseModel):
    account_status: OwnerAccountStatus

    @field_validator("account_status", mode="before")
    @classmethod
    def _strip_status(cls, v: str) -> str:
        return str(v).strip()


class CompanyOwnerPublicRead(BaseModel):
    """Safe owner response (never includes password_hash or otp_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    email: str | None
    last_accepted_terms_date: datetime | None
    is_verified_phone: bool
    join_date: datetime
    account_status: OwnerAccountStatus
    created_at: datetime
    updated_at: datetime


class CompanyOwnerAdminRead(CompanyOwnerPublicRead):
    created_by: UUID | None
    updated_by: UUID | None


class OwnersListFilters(BaseModel):
    account_status: OwnerAccountStatus | None = None
    is_verified_phone: bool | None = None
    join_date_from: datetime | None = None
    join_date_to: datetime | None = None

