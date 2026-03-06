"""Ledger module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.ledger.service import LedgerService


def get_ledger_service(db: DbSession) -> LedgerService:
    return LedgerService(db)


LedgerServiceDep = Annotated[LedgerService, Depends(get_ledger_service)]
