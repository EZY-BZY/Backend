"""Pydantic schemas for company_financials_accounts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyFinancialsAccountVisibilityBody(BaseModel):
    """Toggle whether this account is shown in client-facing UIs."""

    is_visible: bool


class CompanyFinancialsAccountCreate(BaseModel):
    banks_and_wallets_type_id: UUID
    account_number: str = Field(..., min_length=1, max_length=256)
    account_name: str = Field(..., min_length=1, max_length=256)

    @field_validator("account_number", "account_name", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return str(v).strip()


class CompanyFinancialsAccountUpdate(BaseModel):
    banks_and_wallets_type_id: UUID | None = None
    account_number: str | None = Field(None, min_length=1, max_length=256)
    account_name: str | None = Field(None, min_length=1, max_length=256)

    @field_validator("account_number", "account_name", mode="before")
    @classmethod
    def _strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()


class CompanyFinancialsAccountRead(BaseModel):
    """Owner/client API: one linked bank, wallet, or app account for a company."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    banks_and_wallets_type_id: UUID
    account_number: str
    account_name: str
    created_by: UUID
    is_visible: bool
    created_at: datetime
    updated_at: datetime


class CompanyLinkedFinancialAccountRead(CompanyFinancialsAccountRead):
    """Beasy dashboard: same payload, clearer name in OpenAPI (linked bank / wallet / app)."""

    model_config = ConfigDict(
        from_attributes=True,
        title="CompanyLinkedFinancialAccount",
    )
