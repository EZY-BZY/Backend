"""Pydantic schemas for company_financials_accounts."""

from datetime import datetime
from uuid import UUID

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import BankWalletType
from app.modules.company_financials_accounts.models import CompanyFinancialsAccount


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


class BankAndWalletEmbeddedRead(BaseModel):
    """Catalog row linked via ``banks_and_wallets_type_id``."""

    model_config = ConfigDict(from_attributes=True)

    name_ar: str
    name_en: str
    image: str
    kind: BankWalletType


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
    bank_and_wallet: BankAndWalletEmbeddedRead | None = None
    created_at: datetime
    updated_at: datetime


def financial_account_read_dict(row: CompanyFinancialsAccount) -> dict[str, Any]:
    """Serialize account with nested ``bank_and_wallet`` catalog fields when loaded."""
    payload = CompanyFinancialsAccountRead.model_validate(row).model_dump(mode="json")
    catalog = getattr(row, "bank_and_wallet", None)
    if catalog is not None:
        payload["bank_and_wallet"] = BankAndWalletEmbeddedRead.model_validate(catalog).model_dump(
            mode="json"
        )
    return payload


class CompanyLinkedFinancialAccountRead(CompanyFinancialsAccountRead):
    """Beasy dashboard: same payload, clearer name in OpenAPI (linked bank / wallet / app)."""

    model_config = ConfigDict(
        from_attributes=True,
        title="CompanyLinkedFinancialAccount",
    )
