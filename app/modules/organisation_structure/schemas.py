"""Pydantic schemas for organisation structure."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import CompanyEmployeeRole
from app.modules.company_employees.models import CompanyEmployee
from app.modules.organisation_structure.models import OrganisationStructure


def _strip_req(v: str) -> str:
    s = str(v).strip()
    if not s:
        raise ValueError("Value cannot be empty.")
    return s


def _strip_opt(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


class OrganisationStructureCreate(BaseModel):
    name_en: str = Field(..., min_length=1, max_length=256)
    name_ar: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    department_establish_date: date | None = None

    @field_validator("name_en", "name_ar", mode="before")
    @classmethod
    def _strip_names(cls, v: str) -> str:
        return _strip_req(v)

    @field_validator("description", mode="before")
    @classmethod
    def _strip_description(cls, v: str | None) -> str | None:
        return _strip_opt(v)


class OrganisationStructureUpdate(BaseModel):
    name_en: str | None = Field(None, min_length=1, max_length=256)
    name_ar: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = None
    department_establish_date: date | None = None

    @field_validator("name_en", "name_ar", mode="before")
    @classmethod
    def _strip_names(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_req(v)

    @field_validator("description", mode="before")
    @classmethod
    def _strip_description(cls, v: str | None) -> str | None:
        return _strip_opt(v)


class OrganisationStructureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name_en: str
    name_ar: str
    description: str | None
    department_establish_date: date | None
    total_salaries: float
    total_employees: int
    is_deleted: bool
    deleted_at: datetime | None
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime

    @field_validator("total_salaries", mode="before")
    @classmethod
    def _coerce_salaries(cls, v):
        return float(v) if v is not None else 0.0


class OrganisationStructureEmployeeSummary(BaseModel):
    """Employee row on organisation structure detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: CompanyEmployeeRole
    salary: float | None
    bonus_amount: float
    image: str | None

    @field_validator("role", mode="before")
    @classmethod
    def _coerce_role(cls, v):
        if isinstance(v, CompanyEmployeeRole):
            return v
        return CompanyEmployeeRole(v)

    @field_validator("salary", "bonus_amount", mode="before")
    @classmethod
    def _coerce_money(cls, v):
        if v is None:
            return None
        return float(v)


class OrganisationStructureDetailRead(OrganisationStructureRead):
    """Organisation structure with assigned employees (non-deleted first)."""

    employees: list[OrganisationStructureEmployeeSummary] = Field(default_factory=list)


def organisation_structure_detail_dict(
    row: OrganisationStructure,
    employees: list[CompanyEmployee],
) -> dict[str, Any]:
    base = OrganisationStructureRead.model_validate(row).model_dump(mode="json")
    base["employees"] = [
        OrganisationStructureEmployeeSummary.model_validate(emp).model_dump(mode="json")
        for emp in employees
    ]
    return base
