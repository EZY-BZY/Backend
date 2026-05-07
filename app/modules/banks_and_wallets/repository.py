"""Data access for banks_and_wallets."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.banks_and_wallets.models import BankAndWallet


class BankAndWalletRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, row_id: str) -> BankAndWallet | None:
        return self.db.get(BankAndWallet, row_id)

    def list_filtered(
        self,
        *,
        kind: str | None = None,
        is_active: bool | None = None,
    ) -> list[BankAndWallet]:
        stmt = select(BankAndWallet).order_by(BankAndWallet.name_en.asc())
        if kind is not None:
            stmt = stmt.where(BankAndWallet.kind == kind)
        if is_active is not None:
            stmt = stmt.where(BankAndWallet.is_active == is_active)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, row: BankAndWallet) -> BankAndWallet:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: BankAndWallet) -> BankAndWallet:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: BankAndWallet) -> None:
        self.db.delete(row)
        self.db.commit()
