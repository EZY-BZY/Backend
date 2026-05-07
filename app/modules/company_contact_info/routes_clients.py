"""
Clients — **company contact info** (owner CRUD).

**Base path:** ``/clients/companies/{company_id}/contact-info``.

**Auth:** Owner JWT. ``value`` is stored with **all whitespace removed** (spaces, tabs, newlines).

JSON uses the key ``type`` for the channel (see ``CompanyContactChannel`` / ``twitter_x`` for Twitter/X).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.company_contact_info.schemas import (
    CompanyContactInfoCreate,
    CompanyContactInfoRead,
    CompanyContactInfoUpdate,
)
from app.modules.company_contact_info.service import CompanyContactInfoService

router = APIRouter(
    prefix="/companies/{company_id}/contact-info",
    tags=["Company contact info (clients)"],
)


def _svc(db: DbSession) -> CompanyContactInfoService:
    return CompanyContactInfoService(db)


def _dump(row) -> dict:
    return CompanyContactInfoRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[CompanyContactInfoRead]],
    summary="List contact info for a company",
)
def list_company_contact_info(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    items = _svc(db).list_for_owner(str(company_id), current["user_id"])
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [_dump(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "",
    response_model=ApiResponse[CompanyContactInfoRead],
    summary="Add contact info",
)
def create_company_contact_info(
    company_id: UUID,
    data: CompanyContactInfoCreate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).create(str(company_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)


@router.get(
    "/{contact_id}",
    response_model=ApiResponse[CompanyContactInfoRead],
    summary="Get one contact info row",
)
def get_company_contact_info(
    company_id: UUID,
    contact_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    row = _svc(db).get_for_owner(str(company_id), str(contact_id), current["user_id"])
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{contact_id}",
    response_model=ApiResponse[CompanyContactInfoRead],
    summary="Update contact info",
)
def update_company_contact_info(
    company_id: UUID,
    contact_id: UUID,
    data: CompanyContactInfoUpdate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).update(str(company_id), str(contact_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{contact_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete contact info",
)
def delete_company_contact_info(
    company_id: UUID,
    contact_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    ok = _svc(db).delete(str(company_id), str(contact_id), current["user_id"])
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
