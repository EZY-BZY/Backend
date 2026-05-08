"""
Clients — **company branches** (owners and employees with matching ``company_id`` in JWT).

**Base path:** ``/clients/companies/{company_id}/branches``

**Auth:** Client JWT (``account_type`` owner or employee). Employees must have ``company_id``
in the access token matching the path company.

**Delete:** Branch and contact ``DELETE`` endpoints set ``is_active`` to false (soft deactivate).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentClientRequired
from app.modules.company_branches.schemas import (
    CompanyBranchContactCreate,
    CompanyBranchContactRead,
    CompanyBranchContactUpdate,
    CompanyBranchCreate,
    CompanyBranchRead,
    CompanyBranchUpdate,
    CompanyBranchWorkingHoursPut,
    CompanyBranchWorkingHoursRead,
)
from app.modules.company_branches.service import CompanyBranchService

router = APIRouter(
    prefix="/companies/{company_id}/branches",
    tags=["Company branches (clients)"],
)


def _svc(db: DbSession) -> CompanyBranchService:
    return CompanyBranchService(db)


def _dump_branch(row) -> dict:
    return CompanyBranchRead.model_validate(row).model_dump(by_alias=True, mode="json")


def _dump_contact(row) -> dict:
    return CompanyBranchContactRead.model_validate(row).model_dump(by_alias=True, mode="json")


def _dump_hour(row) -> dict:
    return CompanyBranchWorkingHoursRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.post(
    "",
    response_model=ApiResponse[CompanyBranchRead],
    summary="Create a company branch",
)
def create_branch(
    company_id: UUID,
    data: CompanyBranchCreate,
    db: DbSession,
    current: CurrentClientRequired,
):
    try:
        row = _svc(db).create_branch(str(company_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump_branch(row), message=ResponseEnum.SUCCESS.value)


@router.get(
    "",
    response_model=ApiResponse[list[CompanyBranchRead]],
    summary="List my company branches",
)
def list_branches(company_id: UUID, db: DbSession, current: CurrentClientRequired):
    rows = _svc(db).list_branches_client(str(company_id), current)
    return json_success(
        [_dump_branch(x) for x in rows],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{branch_id}",
    response_model=ApiResponse[CompanyBranchRead],
    summary="Get my company branch by id",
)
def get_branch(company_id: UUID, branch_id: UUID, db: DbSession, current: CurrentClientRequired):
    row = _svc(db).get_branch_client(str(company_id), str(branch_id), current)
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_branch(row), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{branch_id}",
    response_model=ApiResponse[CompanyBranchRead],
    summary="Update my company branch",
)
def update_branch(
    company_id: UUID,
    branch_id: UUID,
    data: CompanyBranchUpdate,
    db: DbSession,
    current: CurrentClientRequired,
):
    try:
        row = _svc(db).update_branch(str(company_id), str(branch_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_branch(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{branch_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Deactivate my company branch",
)
def deactivate_branch(company_id: UUID, branch_id: UUID, db: DbSession, current: CurrentClientRequired):
    try:
        ok = _svc(db).deactivate_branch(str(company_id), str(branch_id), current)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Branch deactivated successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/{branch_id}/contacts",
    response_model=ApiResponse[CompanyBranchContactRead],
    summary="Add branch contact number",
)
def add_branch_contact(
    company_id: UUID,
    branch_id: UUID,
    data: CompanyBranchContactCreate,
    db: DbSession,
    current: CurrentClientRequired,
):
    try:
        row = _svc(db).add_contact(str(company_id), str(branch_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump_contact(row), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{branch_id}/contacts/{contact_id}",
    response_model=ApiResponse[CompanyBranchContactRead],
    summary="Update branch contact number",
)
def update_branch_contact(
    company_id: UUID,
    branch_id: UUID,
    contact_id: UUID,
    data: CompanyBranchContactUpdate,
    db: DbSession,
    current: CurrentClientRequired,
):
    try:
        row = _svc(db).update_contact(
            str(company_id), str(branch_id), str(contact_id), current, data
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_contact(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{branch_id}/contacts/{contact_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Deactivate branch contact number",
)
def deactivate_branch_contact(
    company_id: UUID,
    branch_id: UUID,
    contact_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    try:
        ok = _svc(db).deactivate_contact(str(company_id), str(branch_id), str(contact_id), current)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Contact deactivated successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.put(
    "/{branch_id}/working-hours",
    response_model=ApiResponse[list[CompanyBranchWorkingHoursRead]],
    summary="Set full weekly working hours (seven days)",
)
def put_branch_working_hours(
    company_id: UUID,
    branch_id: UUID,
    data: CompanyBranchWorkingHoursPut,
    db: DbSession,
    current: CurrentClientRequired,
):
    try:
        rows = _svc(db).put_working_hours(str(company_id), str(branch_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        [_dump_hour(x) for x in rows],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{branch_id}/working-hours",
    response_model=ApiResponse[list[CompanyBranchWorkingHoursRead]],
    summary="Get branch weekly working hours",
)
def get_branch_working_hours(company_id: UUID, branch_id: UUID, db: DbSession, current: CurrentClientRequired):
    rows = _svc(db).get_working_hours_client(str(company_id), str(branch_id), current)
    if rows is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        [_dump_hour(x) for x in rows],
        message=ResponseEnum.SUCCESS.value,
    )
