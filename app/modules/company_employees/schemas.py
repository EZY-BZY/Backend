"""Pydantic schemas for company employees."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.allenums import CompanyEmployeeRole, CompanySalarySystem

_PHONE_RE = re.compile(r"^\+?[0-9]{6,20}$")


def normalize_phone(v: str) -> str:
    s = re.sub(r"\s+", "", str(v))
    if not _PHONE_RE.match(s):
        raise ValueError("Invalid phone number format.")
    return s


class CompanyEmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=512)
    email: str | None = Field(None, max_length=512)
    password: str = Field(..., min_length=1)
    salary: float | None = Field(None, ge=0)
    bonus_amount: float = Field(0, ge=0)
    salary_system: CompanySalarySystem | None = None
    department: str | None = Field(None, max_length=256)
    role: CompanyEmployeeRole
    app_permission_ids: list[UUID] = Field(
        default_factory=list,
        description="App permission UUIDs to assign (each must exist and be active).",
    )

    @model_validator(mode="after")
    def _unique_permission_ids(self):
        ids = [str(x) for x in self.app_permission_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("app_permission_ids must not contain duplicates.")
        return self

    @field_validator("name", "department", mode="before")
    @classmethod
    def _strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("email", mode="before")
    @classmethod
    def _strip_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class CompanyEmployeeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=512)
    email: str | None = Field(None, max_length=512)
    password: str | None = Field(None, min_length=1)
    salary: float | None = Field(None, ge=0)
    bonus_amount: float | None = Field(None, ge=0)
    salary_system: CompanySalarySystem | None = None
    department: str | None = Field(None, max_length=256)
    role: CompanyEmployeeRole | None = None
    is_active: bool | None = None
    new_app_permission_ids: list[UUID] | None = Field(
        None,
        description="App permission UUIDs to add or reactivate for this employee.",
    )
    removed_app_permission_ids: list[UUID] | None = Field(
        None,
        description="App permission UUIDs to remove (deactivate) for this employee.",
    )

    @model_validator(mode="after")
    def _permission_patch_lists(self):
        new = list(self.new_app_permission_ids or [])
        rem = list(self.removed_app_permission_ids or [])
        new_s = {str(x) for x in new}
        rem_s = {str(x) for x in rem}
        if new_s & rem_s:
            raise ValueError("new_app_permission_ids and removed_app_permission_ids must not overlap.")
        if len(new_s) != len(new):
            raise ValueError("new_app_permission_ids must not contain duplicates.")
        if len(rem_s) != len(rem):
            raise ValueError("removed_app_permission_ids must not contain duplicates.")
        return self

    @field_validator("name", "department", mode="before")
    @classmethod
    def _strip_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("email", mode="before")
    @classmethod
    def _strip_e(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class CompanyEmployeePhoneCreate(BaseModel):
    phone_number: str = Field(..., min_length=6, max_length=64)
    is_primary: bool = False

    @field_validator("phone_number", mode="before")
    @classmethod
    def _norm(cls, v: str) -> str:
        return normalize_phone(v)


class CompanyEmployeePhoneUpdate(BaseModel):
    phone_number: str | None = Field(None, min_length=6, max_length=64)
    is_primary: bool | None = None
    is_active: bool | None = None

    @field_validator("phone_number", mode="before")
    @classmethod
    def _norm_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalize_phone(v)

    @model_validator(mode="after")
    def _primary_implies_active(self):
        if self.is_primary is True and self.is_active is False:
            raise ValueError("Cannot set primary on an inactive phone.")
        return self


class AppPermissionNestedRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    permission_tag: str
    permission_label: str
    permission_key: str
    is_active: bool


class CompanyEmployeePhoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    phone_number: str
    is_primary: bool
    is_active: bool
    created_by_type: str
    created_by_id: UUID | None
    updated_by_type: str
    updated_by_id: UUID | None
    created_at: datetime
    updated_at: datetime


class EmployeeAppPermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    app_permission_id: UUID
    is_active: bool
    assigned_at: datetime
    assigned_by_type: str
    assigned_by_id: UUID | None
    updated_at: datetime
    updated_by_type: str
    updated_by_id: UUID | None
    app_permission: AppPermissionNestedRead


class CompanyEmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name: str
    email: str | None
    salary: float | None
    bonus_amount: float
    salary_system: CompanySalarySystem | None
    department: str | None
    role: CompanyEmployeeRole
    is_active: bool
    created_by_type: str
    created_by_id: UUID | None
    updated_by_type: str
    updated_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    phones: list[CompanyEmployeePhoneRead] = Field(default_factory=list)
    app_permissions: list[EmployeeAppPermissionRead] = Field(default_factory=list)

    @field_validator("role", mode="before")
    @classmethod
    def _coerce_role(cls, v):
        if isinstance(v, CompanyEmployeeRole):
            return v
        return CompanyEmployeeRole(v)

    @field_validator("salary_system", mode="before")
    @classmethod
    def _coerce_salary_sys(cls, v):
        if v is None or isinstance(v, CompanySalarySystem):
            return v
        return CompanySalarySystem(v)

    @field_validator("salary", "bonus_amount", mode="before")
    @classmethod
    def _dec(cls, v):
        if v is None:
            return None
        return float(v)


class CompanyEmployeeBeasyRead(CompanyEmployeeRead):
    model_config = ConfigDict(from_attributes=True, title="CompanyEmployee")

