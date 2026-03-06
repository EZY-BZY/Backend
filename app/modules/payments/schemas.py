"""Payment Pydantic schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentBase(BaseModel):
    to_company_id: UUID
    invoice_id: UUID | None = None
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    reference: str | None = None
    note: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: UUID
    from_company_id: UUID
    created_by_user_id: UUID | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
