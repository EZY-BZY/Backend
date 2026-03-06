"""Invoice Pydantic schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceBase(BaseModel):
    buyer_company_id: UUID
    order_id: UUID | None = None
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    reference: str | None = None
    note: str | None = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceRead(InvoiceBase):
    id: UUID
    seller_company_id: UUID
    buyer_company_id: UUID
    created_by_user_id: UUID | None
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
