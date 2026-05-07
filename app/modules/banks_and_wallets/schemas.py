"""Pydantic schemas for banks_and_wallets."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import BankWalletType


class BankAndWalletCreate(BaseModel):
    name_ar: str = Field(..., min_length=1, max_length=256)
    name_en: str = Field(..., min_length=1, max_length=256, description="Non-Arabic name (e.g. English)")
    image: str = Field(..., max_length=2048)
    country_id: UUID
    kind: BankWalletType = Field(..., description="bank | wallet | app")

    @field_validator("name_ar", "name_en", "image", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return str(v).strip()


class BankAndWalletUpdate(BaseModel):
    name_ar: str | None = Field(None, min_length=1, max_length=256)
    name_en: str | None = Field(None, min_length=1, max_length=256)
    image: str | None = Field(None, max_length=2048)
    country_id: UUID | None = None
    kind: BankWalletType | None = None
    is_active: bool | None = None

    @field_validator("name_ar", "name_en", "image", mode="before")
    @classmethod
    def _strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()


class BankAndWalletRead(BaseModel):
    """Full row for Beasy admin responses (includes ``is_active``)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_ar: str
    name_en: str
    image: str
    country_id: UUID
    kind: BankWalletType
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class BankAndWalletClientRead(BaseModel):
    """Client catalog item: same as Beasy except ``is_active`` is omitted (only active rows are listed)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_ar: str
    name_en: str
    image: str
    country_id: UUID
    kind: BankWalletType
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
