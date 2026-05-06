"""Client auth schemas (owners/employees login)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import ClientAccountType


class ClientLoginRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)
    account_type: ClientAccountType

    @field_validator("phone", mode="before")
    @classmethod
    def _strip_phone(cls, v: str) -> str:
        return str(v).strip()


class OwnerBasicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    email: str | None
    join_date: datetime


class EmployeeBasicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    phone: str | None
    account_type: str


class ClientLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class ForgotPasswordRequestOTP(BaseModel):
    phone: str = Field(..., min_length=1, max_length=64)
    account_type: ClientAccountType

    @field_validator("phone", mode="before")
    @classmethod
    def _strip_phone(cls, v: str) -> str:
        return str(v).strip()


class ForgotPasswordVerifyOTP(BaseModel):
    phone: str = Field(..., min_length=1, max_length=64)
    account_type: ClientAccountType
    otp: str = Field(..., min_length=1, max_length=32)

    @field_validator("phone", "otp", mode="before")
    @classmethod
    def _strip_fields(cls, v: str) -> str:
        return str(v).strip()


class ForgotPasswordChangePassword(BaseModel):
    phone: str = Field(..., min_length=1, max_length=64)
    account_type: ClientAccountType
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @field_validator("phone", mode="before")
    @classmethod
    def _strip_phone(cls, v: str) -> str:
        return str(v).strip()


class ChangePasswordWhileLoggedIn(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


