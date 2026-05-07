"""Pydantic schemas for company_contact_infos."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import CompanyContactChannel


def _strip_all_whitespace(v: str) -> str:
    return re.sub(r"\s+", "", str(v))


class CompanyContactInfoCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=256)
    value: str = Field(..., min_length=1, max_length=2048)
    contact_type: CompanyContactChannel = Field(
        ...,
        alias="type",
        description="number | facebook | instagram | tiktok | youtube | threads | whatsapp | twitter_x",
    )

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("value", mode="before")
    @classmethod
    def _normalize_value(cls, v: str) -> str:
        return _strip_all_whitespace(v)


class CompanyContactInfoUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = Field(None, min_length=1, max_length=256)
    value: str | None = Field(None, min_length=1, max_length=2048)
    contact_type: CompanyContactChannel | None = Field(None, alias="type")

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("value", mode="before")
    @classmethod
    def _normalize_value_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_all_whitespace(v)


class CompanyContactInfoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    company_id: UUID
    title: str
    value: str
    contact_type: CompanyContactChannel = Field(alias="type")
    created_at: datetime
    updated_at: datetime


class CompanyContactInfoBeasyRead(CompanyContactInfoRead):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        title="CompanyContactInfo",
    )
