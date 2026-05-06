"""Pydantic schemas for countries APIs."""

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_name(v: str) -> str:
    return v.strip()


class CountryCreate(BaseModel):
    phone_code: str = Field(..., max_length=16, description="E.g. +20")
    name_en: str = Field(..., max_length=256)
    name_ar: str = Field(..., max_length=256)
    name_fr: str = Field(..., max_length=256)
    phone_regex: str = Field(
        ...,
        max_length=512,
        description="Regex that validates the full phone number (phone_code + phone value).",
    )
    currency_shortcut_en: str = Field(..., max_length=16, description="E.g. USD")
    currency_shortcut_ar: str = Field(..., max_length=16)
    currency_shortcut_fr: str = Field(..., max_length=16)
    currency_name_en: str = Field(..., max_length=128)
    currency_name_ar: str = Field(..., max_length=128)
    currency_name_fr: str = Field(..., max_length=128)
    flag_emoji: str = Field(..., max_length=16, description="Country flag emoji (e.g. 🇪🇬)")

    @field_validator("phone_code", mode="before")
    @classmethod
    def _strip_phone_code(cls, v: str) -> str:
        if v is None:
            return v
        s = str(v).strip()
        return s

    @field_validator("name_en", "name_ar", "name_fr", mode="before")
    @classmethod
    def _strip_names(cls, v: str) -> str:
        return _normalize_name(str(v))

    @field_validator(
        "currency_shortcut_en",
        "currency_shortcut_ar",
        "currency_shortcut_fr",
        "currency_name_en",
        "currency_name_ar",
        "currency_name_fr",
        mode="before",
    )
    @classmethod
    def _strip_currency(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("phone_regex")
    @classmethod
    def _validate_regex(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid phone_regex: {e}") from e
        return v


class CountryUpdate(BaseModel):
    phone_code: str | None = Field(None, max_length=16)
    name_en: str | None = Field(None, max_length=256)
    name_ar: str | None = Field(None, max_length=256)
    name_fr: str | None = Field(None, max_length=256)
    phone_regex: str | None = Field(None, max_length=512)
    currency_shortcut_en: str | None = Field(None, max_length=16)
    currency_shortcut_ar: str | None = Field(None, max_length=16)
    currency_shortcut_fr: str | None = Field(None, max_length=16)
    currency_name_en: str | None = Field(None, max_length=128)
    currency_name_ar: str | None = Field(None, max_length=128)
    currency_name_fr: str | None = Field(None, max_length=128)
    flag_emoji: str | None = Field(None, max_length=16)

    @field_validator("phone_code", mode="before")
    @classmethod
    def _strip_phone_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("name_en", "name_ar", "name_fr", mode="before")
    @classmethod
    def _strip_names(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _normalize_name(str(v))

    @field_validator(
        "currency_shortcut_en",
        "currency_shortcut_ar",
        "currency_shortcut_fr",
        "currency_name_en",
        "currency_name_ar",
        "currency_name_fr",
        "flag_emoji",
        mode="before",
    )
    @classmethod
    def _strip_misc(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("phone_regex")
    @classmethod
    def _validate_regex(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid phone_regex: {e}") from e
        return v


class CountryPublicRead(BaseModel):
    """Public list/detail: no audit metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    phone_code: str
    name_en: str
    name_ar: str
    name_fr: str
    phone_regex: str
    currency_shortcut_en: str
    currency_shortcut_ar: str
    currency_shortcut_fr: str
    currency_name_en: str
    currency_name_ar: str
    currency_name_fr: str
    flag_emoji: str
    created_date: date


class CountryRead(BaseModel):
    """Full row for Beasy admin responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    phone_code: str
    name_en: str
    name_ar: str
    name_fr: str
    phone_regex: str
    currency_shortcut_en: str
    currency_shortcut_ar: str
    currency_shortcut_fr: str
    currency_name_en: str
    currency_name_ar: str
    currency_name_fr: str
    flag_emoji: str
    created_date: date
    created_by: str | None
    created_at: datetime
    updated_by: str | None
    updated_at: datetime

