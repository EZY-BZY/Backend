"""Business logic for banks_and_wallets catalog."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.allenums import BankWalletType
from app.modules.banks_and_wallets.models import BankAndWallet
from app.modules.banks_and_wallets.repository import BankAndWalletRepository
from app.modules.banks_and_wallets.schemas import BankAndWalletCreate, BankAndWalletUpdate


class BankAndWalletService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = BankAndWalletRepository(db)

    def list_catalog(
        self,
        *,
        kind: BankWalletType | None = None,
        is_active: bool | None = None,
    ) -> list[BankAndWallet]:
        return self._repo.list_filtered(
            kind=kind.value if kind is not None else None,
            is_active=is_active,
        )

    def create(self, data: BankAndWalletCreate, actor_id: str) -> BankAndWallet:
        row = BankAndWallet(
            name_ar=data.name_ar,
            name_en=data.name_en,
            image=data.image,
            country_id=str(data.country_id),
            kind=data.kind.value,
            created_by=actor_id,
            is_active=True,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create bank/wallet (invalid country or constraint).") from e

    def update(self, row_id: str, data: BankAndWalletUpdate) -> BankAndWallet | None:
        row = self._repo.get_by_id(row_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        if "kind" in payload and payload["kind"] is not None:
            row.kind = payload["kind"].value
            del payload["kind"]
        if "is_active" in payload and payload["is_active"] is not None:
            row.is_active = payload["is_active"]
            del payload["is_active"]
        if "country_id" in payload and payload["country_id"] is not None:
            row.country_id = str(payload["country_id"])
            del payload["country_id"]
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            return self._repo.update(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update bank/wallet.") from e

    def delete(self, row_id: str) -> bool:
        row = self._repo.get_by_id(row_id)
        if row is None:
            return False
        try:
            self._repo.delete(row)
        except IntegrityError:
            self._db.rollback()
            raise ValueError("Cannot delete: referenced by company financial accounts.") from None
        return True
