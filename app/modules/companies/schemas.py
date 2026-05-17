"""Pydantic schemas for companies."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import CompanyServiceType, CompanyStatus

if TYPE_CHECKING:
    from app.modules.companies.models import Company

_TAX_NUMBER_RE = re.compile(r"\D")


def normalize_tax_number(value: str | int | None) -> str | None:
    """Keep digits only; spaces, dashes, and other characters are removed."""
    if value is None:
        return None
    digits = _TAX_NUMBER_RE.sub("", str(value).strip())
    return digits or None


class CompanyCreate(BaseModel):
    """Fields allowed when creating a company (client)."""

    image: str | None = Field(None, max_length=2048)
    company_name_ar: str = Field(..., min_length=1, max_length=256)
    company_name_en: str | None = Field(None, max_length=256)
    company_description_ar: str = Field(..., min_length=1)
    company_description_en: str | None = None
    current_balance: float = Field(
        ...,
        description="Signed balance; may be negative. Stored with high precision in the database.",
    )
    service: CompanyServiceType
    tax_number: str | int | None = Field(
        None,
        max_length=128,
        description="Digits only in storage; spaces, dashes, and other separators are stripped on save.",
    )
    industry_ids: list[UUID] = Field(
        default_factory=list,
        description="Industries this company serves (must exist in the industries catalog).",
    )

    @field_validator("tax_number", mode="before")
    @classmethod
    def _normalize_tax_number(cls, v: str | int | None) -> str | None:
        return normalize_tax_number(v)

    @field_validator("industry_ids", mode="after")
    @classmethod
    def _dedupe_industry_ids(cls, v: list[UUID]) -> list[UUID]:
        return list(dict.fromkeys(v))

    @field_validator("company_name_ar", mode="before")
    @classmethod
    def _strip_name_ar(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("company_description_ar", "company_description_en", mode="before")
    @classmethod
    def _strip_descriptions(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("company_name_ar", "company_name_en", "image", mode="before")
    @classmethod
    def _strip_optional_strings(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class CompanyUpdate(BaseModel):
    """Partial update for company (client)."""

    image: str | None = Field(None, max_length=2048)
    company_name_ar: str | None = Field(None, min_length=1, max_length=256)
    company_name_en: str | None = Field(None, max_length=256)
    company_description_ar: str | None = Field(None, min_length=1)
    company_description_en: str | None = None
    current_balance: float | None = Field(
        None,
        description="Signed balance; may be negative.",
    )
    service: CompanyServiceType | None = None
    tax_number: str | int | None = Field(
        None,
        max_length=128,
        description="Digits only in storage; spaces, dashes, and other separators are stripped on save.",
    )
    status: CompanyStatus | None = None
    industry_ids: list[UUID] | None = Field(
        None,
        description="If set, replaces the full list of industries for this company.",
    )

    @field_validator("tax_number", mode="before")
    @classmethod
    def _normalize_tax_number_u(cls, v: str | int | None) -> str | None:
        return normalize_tax_number(v)

    @field_validator("industry_ids", mode="after")
    @classmethod
    def _dedupe_industry_ids_u(cls, v: list[UUID] | None) -> list[UUID] | None:
        if v is None:
            return None
        return list(dict.fromkeys(v))

    @field_validator("company_name_ar", mode="before")
    @classmethod
    def _strip_name_ar_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("company_description_ar", "company_description_en", mode="before")
    @classmethod
    def _strip_descriptions_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("company_name_ar", "company_name_en", "image", mode="before")
    @classmethod
    def _strip_optional_strings_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class CompanyChangeVisibilityBody(BaseModel):
    """Toggle what sections are shown on the company profile."""

    show_products: bool
    show_social_media: bool
    show_contact_info: bool
    show_branches: bool


class CompanyRead(BaseModel):
    """Full company row for API responses (no secrets)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    company_name_ar: str
    company_name_en: str | None
    company_description_ar: str
    company_description_en: str | None
    show_branches: bool
    show_products: bool
    show_social_media: bool
    show_contact_info: bool
    status: CompanyStatus
    image: str | None
    service: CompanyServiceType
    current_balance: float 
    tax_number: str | None
    industry_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


def company_read_dict(company: Company, industry_ids: list[str]) -> dict:
    """Build API payload including ``industry_ids`` (stored in ``company_industries``)."""
    d = CompanyRead.model_validate(company).model_dump(mode="json")
    d["industry_ids"] = [UUID(x) for x in industry_ids]
    return d
