"""Product Pydantic schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., max_length=256)
    sku: str | None = None
    description: str | None = None
    unit_price: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=256)
    sku: str | None = None
    description: str | None = None
    unit_price: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=3)
    is_active: bool | None = None


class ProductRead(ProductBase):
    id: UUID
    company_id: UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
