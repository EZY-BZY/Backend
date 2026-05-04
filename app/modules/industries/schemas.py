"""Pydantic schemas for industries APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IndustryCreate(BaseModel):
    name_en: str = Field(..., max_length=256)
    name_ar: str = Field(..., max_length=256)
    name_fr: str = Field(..., max_length=256)
    image: str = Field(..., max_length=2048, description="Path or URL from media upload")


class IndustryUpdate(BaseModel):
    name_en: str | None = Field(None, max_length=256)
    name_ar: str | None = Field(None, max_length=256)
    name_fr: str | None = Field(None, max_length=256)
    image: str | None = Field(None, max_length=2048)


class IndustryPublicRead(BaseModel):
    """Public list/detail: no audit metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name_en: str
    name_ar: str
    name_fr: str
    image: str


class IndustryRead(BaseModel):
    """Full row for Beasy admin responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name_en: str
    name_ar: str
    name_fr: str
    image: str
    created_by: str | None
    created_at: datetime
    updated_by: str | None
    updated_at: datetime
