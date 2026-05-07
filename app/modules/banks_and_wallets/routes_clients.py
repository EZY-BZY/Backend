"""
Clients — **read-only** banks / wallets / apps catalog.

**Docs:** OpenAPI shows this under ``/clients/banks-and-wallets``; no auth header required
so mobile apps can populate dropdowns before login.

**Payload:** Only **active** rows; response schema **excludes** ``is_active`` (Beasy-only field).
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.common.allenums import BankWalletType, ResponseEnum
from app.common.api_response import ApiResponse, json_success
from app.db.session import DbSession
from app.modules.banks_and_wallets.schemas import BankAndWalletClientRead
from app.modules.banks_and_wallets.service import BankAndWalletService

router = APIRouter(prefix="/banks-and-wallets", tags=["Banks & wallets (clients)"])


def _svc(db: DbSession) -> BankAndWalletService:
    return BankAndWalletService(db)


@router.get(
    "",
    response_model=ApiResponse[list[BankAndWalletClientRead]],
    summary="List banks, wallets, and apps (public)",
    description=(
        "Unauthenticated catalog. **Inactive** catalog rows are never returned. "
        "Optional ``kind`` query: ``bank``, ``wallet``, or ``app``."
    ),
)
def list_banks_and_wallets_public(
    db: DbSession,
    kind: BankWalletType | None = Query(None, description="Filter by bank | wallet | app"),
):
    items = _svc(db).list_catalog(
        kind=kind,
        is_active=True,
    )
    return json_success(
        [BankAndWalletClientRead.model_validate(x).model_dump() for x in items],
        message=ResponseEnum.SUCCESS.value,
    )
