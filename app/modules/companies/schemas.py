"""Pydantic schemas for companies."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import CompanyServiceType, CompanyStatus


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
    tax_number: str | None = Field(None, max_length=128)

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

    @field_validator(
        "company_name_ar",
        "company_name_en",
        "tax_number",
        "image",
        mode="before",
    )
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
    tax_number: str | None = Field(None, max_length=128)
    status: CompanyStatus | None = None

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

    @field_validator(
        "company_name_ar",
        "company_name_en",
        "tax_number",
        "image",
        mode="before",
    )
    @classmethod
    def _strip_optional_strings(cls, v: str | None) -> str | None:
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
    created_at: datetime
    updated_at: datetime
