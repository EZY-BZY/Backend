"""Ledger entry Pydantic schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class LedgerEntryBase(BaseModel):
    to_company_id: UUID
    source_type: str = Field(..., max_length=64)
    source_id: UUID | None = None
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    note: str | None = None


class LedgerEntryCreate(LedgerEntryBase):
    pass


class LedgerEntryRead(LedgerEntryBase):
    id: UUID
    from_company_id: UUID
    created_by_user_id: UUID | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
