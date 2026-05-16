"""Pydantic schemas for company employees."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.allenums import CompanyBranchType, CompanyEmployeeRole, CompanySalarySystem
from app.modules.company_employees.models import CompanyEmployee

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
    organisation_structure_id: UUID | None = Field(
        None,
        description="Organisation structure / department UUID (must belong to the same company).",
    )
    role: CompanyEmployeeRole
    app_permission_ids: list[UUID] = Field(
        default_factory=list,
        description="App permission UUIDs to assign (each must exist and be active).",
    )
    branch_ids: list[UUID] = Field(
        default_factory=list,
        description="Branch UUIDs where this employee works (must belong to the same company).",
    )

    @model_validator(mode="after")
    def _unique_permission_ids(self):
        ids = [str(x) for x in self.app_permission_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("app_permission_ids must not contain duplicates.")
        branch_ids = [str(x) for x in self.branch_ids]
        if len(branch_ids) != len(set(branch_ids)):
            raise ValueError("branch_ids must not contain duplicates.")
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
    organisation_structure_id: UUID | None = Field(
        None,
        description="Organisation structure / department UUID (must belong to the same company).",
    )
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
    new_branch_ids: list[UUID] | None = Field(
        None,
        description="Branch UUIDs to assign (must belong to the same company).",
    )
    removed_branch_ids: list[UUID] | None = Field(
        None,
        description="Branch UUIDs to unassign from this employee.",
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
        new_b = list(self.new_branch_ids or [])
        rem_b = list(self.removed_branch_ids or [])
        new_bs = {str(x) for x in new_b}
        rem_bs = {str(x) for x in rem_b}
        if new_bs & rem_bs:
            raise ValueError("new_branch_ids and removed_branch_ids must not overlap.")
        if len(new_bs) != len(new_b):
            raise ValueError("new_branch_ids must not contain duplicates.")
        if len(rem_bs) != len(rem_b):
            raise ValueError("removed_branch_ids must not contain duplicates.")
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


class EmployeeBranchNestedRead(BaseModel):
    """Branch summary on an employee record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_name: str
    branch_type: CompanyBranchType

    @field_validator("branch_type", mode="before")
    @classmethod
    def _coerce_branch_type(cls, v):
        if isinstance(v, CompanyBranchType):
            return v
        return CompanyBranchType(v)
    is_active: bool
    is_visible_to_clients: bool
    is_deleted: bool
    deleted_at: datetime | None


class CompanyEmployeeBranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    branch_id: UUID
    created_by_type: str
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    branch: EmployeeBranchNestedRead | None = None


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


class CompanyEmployeeBaseRead(BaseModel):
    """Core employee fields + phones/permissions (no branch relations on ORM)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name: str
    email: str | None
    salary: float | None
    bonus_amount: float
    salary_system: CompanySalarySystem | None
    department: str | None
    organisation_structure_id: UUID | None
    role: CompanyEmployeeRole
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
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


class CompanyEmployeeRead(CompanyEmployeeBaseRead):
    """Client/Beasy response; ``branches`` lists assigned locations (see ``employee_read_dict``)."""

    branches: list[EmployeeBranchNestedRead] = Field(default_factory=list)


class CompanyEmployeeBeasyRead(CompanyEmployeeRead):
    model_config = ConfigDict(from_attributes=True, title="CompanyEmployee")


def employee_read_dict(row: CompanyEmployee) -> dict:
    """Serialize employee with deduped ``branches`` (each item includes ``id``)."""
    d = CompanyEmployeeBaseRead.model_validate(row).model_dump(mode="json")
    seen: set[str] = set()
    branches: list[dict] = []
    for link in getattr(row, "branch_assignments", []) or []:
        bid = str(link.branch_id)
        if bid in seen:
            continue
        seen.add(bid)
        if link.branch is not None:
            branches.append(
                EmployeeBranchNestedRead.model_validate(link.branch).model_dump(mode="json")
            )
    d["branches"] = branches
    return d

