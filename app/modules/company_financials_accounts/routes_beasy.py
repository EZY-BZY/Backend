"""
Beasy — **company linked financial accounts** (banks, wallets, apps).

**Base path:** ``/beasy/companies/{company_id}/financial-accounts``

**Auth:** Beasy employee JWT.

**Scope:** Lists and reads accounts **for a single company** (matches how owners manage
them under ``/clients/companies/{company_id}/financial-accounts``).

**OpenAPI:** Response schema title ``CompanyLinkedFinancialAccount`` for clearer docs.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.company_financials_accounts.schemas import (
    CompanyLinkedFinancialAccountRead,
    CompanyFinancialsAccountVisibilityBody,
)
from app.modules.company_financials_accounts.service import CompanyFinancialsAccountService

router = APIRouter(
    prefix="/companies/{company_id}/financial-accounts",
    tags=["Company linked accounts (Beasy)"],
)


def _svc(db: DbSession) -> CompanyFinancialsAccountService:
    return CompanyFinancialsAccountService(db)


@router.get(
    "",
    response_model=ApiResponse[list[CompanyLinkedFinancialAccountRead]],
    summary="List a company's linked bank / wallet / app accounts",
    description=(
        "Returns every financial account row registered for ``company_id`` "
        "(newest first). 404 if the company id does not exist."
    ),
)
def list_company_linked_financial_accounts(
    company_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    items = _svc(db).list_for_company_admin(str(company_id))
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [CompanyLinkedFinancialAccountRead.model_validate(x).model_dump() for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{account_id}",
    response_model=ApiResponse[CompanyLinkedFinancialAccountRead],
    summary="Get one linked account for this company",
    description=(
        "Loads the account only if ``account_id`` belongs to ``company_id``. "
        "404 if company is unknown, account is missing, or ids do not match."
    ),
)
def get_company_linked_financial_account(
    company_id: UUID,
    account_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    row = _svc(db).get_for_company_admin(str(company_id), str(account_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        CompanyLinkedFinancialAccountRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{account_id}/visibility",
    response_model=ApiResponse[CompanyLinkedFinancialAccountRead],
    summary="Set linked account visibility (Beasy)",
    description="Same semantics as the owner visibility toggle; used for support or admin workflows.",
)
def set_company_linked_financial_account_visibility(
    company_id: UUID,
    account_id: UUID,
    data: CompanyFinancialsAccountVisibilityBody,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    row = _svc(db).set_visibility_for_admin(str(company_id), str(account_id), data)
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        CompanyLinkedFinancialAccountRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
