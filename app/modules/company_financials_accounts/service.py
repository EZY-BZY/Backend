"""Business logic for company financial accounts."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.banks_and_wallets.repository import BankAndWalletRepository
from app.modules.company_financials_accounts.models import CompanyFinancialsAccount
from app.modules.company_financials_accounts.repository import CompanyFinancialsAccountRepository
from app.modules.company_financials_accounts.schemas import (
    CompanyFinancialsAccountCreate,
    CompanyFinancialsAccountUpdate,
    CompanyFinancialsAccountVisibilityBody,
)
from app.modules.companies.service import CompanyService


class CompanyFinancialsAccountService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyFinancialsAccountRepository(db)
        self._banks = BankAndWalletRepository(db)
        self._companies = CompanyService(db)

    def list_for_company_admin(self, company_id: str) -> list[CompanyFinancialsAccount] | None:
        """Beasy: list accounts for a company. Returns None if company does not exist."""
        if self._companies.get_company_by_id(company_id) is None:
            return None
        return self._repo.list_for_company(company_id)

    def get_for_company_admin(
        self,
        company_id: str,
        account_id: str,
    ) -> CompanyFinancialsAccount | None:
        """Beasy: get one account; ensures it belongs to ``company_id``."""
        if self._companies.get_company_by_id(company_id) is None:
            return None
        row = self._repo.get_by_id(account_id)
        if row is None or row.company_id != company_id:
            return None
        return row

    def list_for_company(
        self, company_id: str, owner_id: str
    ) -> list[CompanyFinancialsAccount] | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        return self._repo.list_for_company(company_id, load_catalog=True)

    def get_for_owner(
        self,
        company_id: str,
        account_id: str,
        owner_id: str,
    ) -> CompanyFinancialsAccount | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        row = self._repo.get_by_id(account_id, load_catalog=True)
        if row is None or row.company_id != company_id:
            return None
        return row

    def create(
        self,
        company_id: str,
        owner_id: str,
        data: CompanyFinancialsAccountCreate,
    ) -> CompanyFinancialsAccount:
        if self._companies.get_company(company_id, owner_id) is None:
            raise ValueError("Company not found or not owned by you.")
        if self._banks.get_by_id(str(data.banks_and_wallets_type_id)) is None:
            raise ValueError("Invalid banks_and_wallets id.")
        row = CompanyFinancialsAccount(
            company_id=company_id,
            banks_and_wallets_type_id=str(data.banks_and_wallets_type_id),
            account_number=data.account_number,
            account_name=data.account_name,
            created_by=owner_id,
            is_visible=True,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create financial account.") from e

    def update(
        self,
        company_id: str,
        account_id: str,
        owner_id: str,
        data: CompanyFinancialsAccountUpdate,
    ) -> CompanyFinancialsAccount | None:
        row = self.get_for_owner(company_id, account_id, owner_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        if "banks_and_wallets_type_id" in payload and payload["banks_and_wallets_type_id"] is not None:
            bid = str(payload["banks_and_wallets_type_id"])
            if self._banks.get_by_id(bid) is None:
                raise ValueError("Invalid banks_and_wallets id.")
            row.banks_and_wallets_type_id = bid
            del payload["banks_and_wallets_type_id"]
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            return self._repo.update(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update financial account.") from e

    def delete(self, company_id: str, account_id: str, owner_id: str) -> bool:
        row = self.get_for_owner(company_id, account_id, owner_id)
        if row is None:
            return False
        self._repo.delete(row)
        return True

    def set_visibility_for_owner(
        self,
        company_id: str,
        account_id: str,
        owner_id: str,
        body: CompanyFinancialsAccountVisibilityBody,
    ) -> CompanyFinancialsAccount | None:
        row = self.get_for_owner(company_id, account_id, owner_id)
        if row is None:
            return None
        row.is_visible = body.is_visible
        return self._repo.update(row)

    def set_visibility_for_admin(
        self,
        company_id: str,
        account_id: str,
        body: CompanyFinancialsAccountVisibilityBody,
    ) -> CompanyFinancialsAccount | None:
        row = self.get_for_company_admin(company_id, account_id)
        if row is None:
            return None
        row.is_visible = body.is_visible
        return self._repo.update(row)
