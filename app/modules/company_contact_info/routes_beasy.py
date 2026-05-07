"""
Beasy — read **company contact info** for a company.

**Base path:** ``/beasy/companies/{company_id}/contact-info``

**Auth:** Beasy employee JWT. OpenAPI schema title ``CompanyContactInfo``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.company_contact_info.schemas import CompanyContactInfoBeasyRead
from app.modules.company_contact_info.service import CompanyContactInfoService

router = APIRouter(
    prefix="/companies/{company_id}/contact-info",
    tags=["Company contact info (Beasy) Ignore for now"],
)


def _svc(db: DbSession) -> CompanyContactInfoService:
    return CompanyContactInfoService(db)


def _dump(row) -> dict:
    return CompanyContactInfoBeasyRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[CompanyContactInfoBeasyRead]],
    summary="List a company's contact info",
)
def list_company_contact_info_beasy(
    company_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    items = _svc(db).list_for_company_admin(str(company_id))
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [_dump(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{contact_id}",
    response_model=ApiResponse[CompanyContactInfoBeasyRead],
    summary="Get one contact info row",
)
def get_company_contact_info_beasy(
    company_id: UUID,
    contact_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    row = _svc(db).get_for_company_admin(str(company_id), str(contact_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)
