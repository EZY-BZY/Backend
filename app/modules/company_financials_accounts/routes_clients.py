"""
Clients — **company financial accounts** (owner CRUD).

**Base path:** ``/clients/companies/{company_id}/financial-accounts``.

**Auth:** Owner JWT only (``CurrentOwnerRequired``); ``company_id`` must belong to the token user.

**Fields:** ``banks_and_wallets_type_id`` references a row in ``banks_and_wallets`` (the catalog).
``created_by`` is set server-side to the owner id.

**OpenAPI:** Register this router after ``companies_clients_router`` so paths stay grouped;
FastAPI still resolves ``.../financial-accounts`` vs ``.../{{company_id}}`` correctly.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.company_financials_accounts.schemas import (
    CompanyFinancialsAccountCreate,
    CompanyFinancialsAccountRead,
    CompanyFinancialsAccountUpdate,
    CompanyFinancialsAccountVisibilityBody,
    financial_account_read_dict,
)
from app.modules.company_financials_accounts.service import CompanyFinancialsAccountService

router = APIRouter(
    prefix="/companies/{company_id}/financial-accounts",
    tags=["Company financial accounts (clients)"],
)


def _svc(db: DbSession) -> CompanyFinancialsAccountService:
    return CompanyFinancialsAccountService(db)


@router.get(
    "",
    response_model=ApiResponse[list[CompanyFinancialsAccountRead]],
    summary="List accounts for one company",
    description=(
        "404 if ``company_id`` is missing or not owned by the authenticated owner. "
        "Each item includes nested ``bank_and_wallet`` (``name_ar``, ``name_en``, ``image``, ``kind``)."
    ),
)
def list_financial_accounts(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    items = _svc(db).list_for_company(str(company_id), current["user_id"])
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [financial_account_read_dict(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "",
    response_model=ApiResponse[CompanyFinancialsAccountRead],
    summary="Add a financial account",
    description="``banks_and_wallets_type_id`` must exist in the banks & wallets catalog.",
)
def create_financial_account(
    company_id: UUID,
    data: CompanyFinancialsAccountCreate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).create(str(company_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        CompanyFinancialsAccountRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{account_id}",
    response_model=ApiResponse[CompanyFinancialsAccountRead],
    summary="Get one account",
    description=(
        "404 if the company is not yours, the account id is wrong, or the account belongs to another company. "
        "Includes nested ``bank_and_wallet`` (``name_ar``, ``name_en``, ``image``, ``kind``)."
    ),
)
def get_financial_account(
    company_id: UUID,
    account_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    row = _svc(db).get_for_owner(str(company_id), str(account_id), current["user_id"])
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        financial_account_read_dict(row),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{account_id}",
    response_model=ApiResponse[CompanyFinancialsAccountRead],
    summary="Update an account",
    description="Partial body; validates new ``banks_and_wallets_type_id`` when provided.",
)
def update_financial_account(
    company_id: UUID,
    account_id: UUID,
    data: CompanyFinancialsAccountUpdate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).update(str(company_id), str(account_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        CompanyFinancialsAccountRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{account_id}/visibility",
    response_model=ApiResponse[CompanyFinancialsAccountRead],
    summary="Set account visibility",
    description="When ``is_visible`` is false, the account may be omitted from public-facing listings.",
)
def set_financial_account_visibility(
    company_id: UUID,
    account_id: UUID,
    data: CompanyFinancialsAccountVisibilityBody,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    row = _svc(db).set_visibility_for_owner(
        str(company_id), str(account_id), current["user_id"], data
    )
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        CompanyFinancialsAccountRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete(
    "/{account_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete an account",
    description="Permanent delete for that company’s row; id must belong to ``company_id`` and owner.",
)
def delete_financial_account(
    company_id: UUID,
    account_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    ok = _svc(db).delete(str(company_id), str(account_id), current["user_id"])
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
