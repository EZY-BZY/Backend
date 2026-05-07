"""Pydantic schemas for fixed assets and assets_media."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import FixedAssetType


class FixedAssetMediaCreate(BaseModel):
    media_type: str = Field(..., min_length=1, max_length=64)
    media_link: str = Field(..., min_length=1, max_length=2048)

    @field_validator("media_type", "media_link", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return str(v).strip()


class FixedAssetMediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    media_type: str
    media_link: str
    created_at: datetime
    updated_at: datetime


class FixedAssetCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_name: str = Field(..., min_length=1, max_length=512)
    asset_type: FixedAssetType = Field(
        ...,
        alias="type",
        description="cars_and_trucks | building_and_real_estate | machines | computers | office_furniture | other",
    )
    details: str = Field(..., min_length=1)
    location_description: str = Field(..., min_length=1)

    @field_validator("asset_name", mode="before")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("details", "location_description", mode="before")
    @classmethod
    def _strip_text(cls, v: str) -> str:
        return str(v).strip()


class FixedAssetUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_name: str | None = Field(None, min_length=1, max_length=512)
    asset_type: FixedAssetType | None = Field(None, alias="type")
    details: str | None = Field(None, min_length=1)
    location_description: str | None = Field(None, min_length=1)

    @field_validator("asset_name", mode="before")
    @classmethod
    def _strip_name_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("details", "location_description", mode="before")
    @classmethod
    def _strip_text_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()


class FixedAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    company_id: UUID
    asset_name: str
    asset_type: FixedAssetType = Field(alias="type")
    details: str
    location_description: str
    media: list[FixedAssetMediaRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class FixedAssetBeasyRead(FixedAssetRead):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        title="CompanyFixedAsset",
    )
