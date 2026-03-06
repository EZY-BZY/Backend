"""Order Pydantic schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemBase(BaseModel):
    product_id: UUID | None = None
    description: str = Field(..., max_length=512)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    id: UUID
    order_id: UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class OrderBase(BaseModel):
    seller_company_id: UUID
    reference: str | None = None
    note: str | None = None


class OrderCreate(OrderBase):
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: str | None = None
    reference: str | None = None
    note: str | None = None


class OrderRead(OrderBase):
    id: UUID
    buyer_company_id: UUID
    seller_company_id: UUID
    created_by_user_id: UUID | None
    status: str
    created_at: str
    updated_at: str
    items: list[OrderItemRead] = []

    model_config = {"from_attributes": True}
