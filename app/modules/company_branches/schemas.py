"""Pydantic schemas for company branches."""

from __future__ import annotations

import re
from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.allenums import CompanyBranchType, Weekday

_PHONE_RE = re.compile(r"^\+?[0-9]{6,20}$")


class CompanyBranchCreate(BaseModel):
    branch_name: str = Field(..., min_length=1, max_length=512)
    branch_location_description: str | None = Field(None, max_length=8192)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    branch_type: CompanyBranchType
    is_visible_to_clients: bool = True

    @field_validator("branch_name", "branch_location_description", mode="before")
    @classmethod
    def _strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @model_validator(mode="after")
    def _lat_lon_pair(self):
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("Provide both latitude and longitude, or neither.")
        return self


class CompanyBranchUpdate(BaseModel):
    branch_name: str | None = Field(None, min_length=1, max_length=512)
    branch_location_description: str | None = Field(None, max_length=8192)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    branch_type: CompanyBranchType | None = None
    is_active: bool | None = None
    is_visible_to_clients: bool | None = None

    @field_validator("branch_name", "branch_location_description", mode="before")
    @classmethod
    def _strip_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @model_validator(mode="after")
    def _lat_lon_pair(self):
        if self.latitude is None and self.longitude is None:
            return self
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("Provide both latitude and longitude, or neither.")
        return self


class CompanyBranchContactCreate(BaseModel):
    contact_name: str = Field(..., min_length=1, max_length=256)
    phone_number: str = Field(..., min_length=6, max_length=64)
    is_primary: bool = False

    @field_validator("contact_name", mode="before")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("phone_number", mode="before")
    @classmethod
    def _normalize_phone(cls, v: str) -> str:
        s = re.sub(r"\s+", "", str(v))
        if not _PHONE_RE.match(s):
            raise ValueError("Invalid phone number format.")
        return s


class CompanyBranchContactUpdate(BaseModel):
    contact_name: str | None = Field(None, min_length=1, max_length=256)
    phone_number: str | None = Field(None, min_length=6, max_length=64)
    is_primary: bool | None = None
    is_active: bool | None = None

    @field_validator("contact_name", mode="before")
    @classmethod
    def _strip_n(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("phone_number", mode="before")
    @classmethod
    def _normalize_phone_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = re.sub(r"\s+", "", str(v))
        if not _PHONE_RE.match(s):
            raise ValueError("Invalid phone number format.")
        return s


class CompanyBranchWorkingHourItem(BaseModel):
    day_of_week: Weekday
    is_day_off: bool = False
    opening_time: time | None = None
    closing_time: time | None = None

    @model_validator(mode="after")
    def _times_rule(self):
        if self.is_day_off:
            if self.opening_time is not None or self.closing_time is not None:
                raise ValueError("opening_time and closing_time must be empty when is_day_off is true.")
            return self
        if self.opening_time is None or self.closing_time is None:
            raise ValueError("opening_time and closing_time are required when is_day_off is false.")
        if self.closing_time <= self.opening_time:
            raise ValueError("closing_time must be after opening_time.")
        return self


class CompanyBranchWorkingHoursPut(BaseModel):
    """Replace the full weekly schedule (seven rows, one per weekday)."""

    hours: list[CompanyBranchWorkingHourItem] = Field(..., min_length=7, max_length=7)

    @model_validator(mode="after")
    def _all_weekdays_once(self):
        got = {h.day_of_week for h in self.hours}
        if got != set(Weekday):
            raise ValueError("Must include exactly one entry per weekday (Saturday through Friday).")
        return self


class CompanyBranchContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    contact_name: str
    phone_number: str
    is_primary: bool
    is_active: bool
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class CompanyBranchWorkingHoursRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    day_of_week: Weekday
    is_day_off: bool
    opening_time: time | None
    closing_time: time | None
    is_active: bool
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime

    @field_validator("day_of_week", mode="before")
    @classmethod
    def _coerce_weekday(cls, v):
        if isinstance(v, Weekday):
            return v
        return Weekday(v)


class CompanyBranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    branch_name: str
    branch_location_description: str | None
    latitude: float | None
    longitude: float | None
    branch_type: CompanyBranchType
    is_active: bool
    is_visible_to_clients: bool
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime
    contacts: list[CompanyBranchContactRead] = Field(default_factory=list)
    working_hours: list[CompanyBranchWorkingHoursRead] = Field(default_factory=list)

    @field_validator("branch_type", mode="before")
    @classmethod
    def _coerce_branch_type(cls, v):
        if isinstance(v, CompanyBranchType):
            return v
        return CompanyBranchType(v)

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def _numeric_to_float(cls, v):
        if v is None:
            return None
        return float(v)


class CompanyBranchBeasyRead(CompanyBranchRead):
    model_config = ConfigDict(from_attributes=True, title="CompanyBranch")
