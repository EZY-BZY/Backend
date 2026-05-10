"""
Clients — **company employees** (owners or company admins only).

**Base path:** ``/clients/companies/{company_id}/employees``

**Auth:** Owner JWT, or company-employee JWT with ``role=admin`` (see ``/clients/auth/login``).

**App permissions:** pass ``app_permission_ids`` on **create**. On **patch**, use ``new_app_permission_ids``
and ``removed_app_permission_ids`` (omit both keys to leave permissions unchanged).

**Deactivate:** ``DELETE`` on employee or phone sets ``is_active`` to false.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.company_employees.dependencies import CurrentEmployerRequired
from app.modules.company_employees.schemas import (
    CompanyEmployeeCreate,
    CompanyEmployeePhoneCreate,
    CompanyEmployeePhoneRead,
    CompanyEmployeePhoneUpdate,
    CompanyEmployeeRead,
    EmployeeAppPermissionRead,
    CompanyEmployeeUpdate,
)
from app.modules.company_employees.service import CompanyEmployeeService

router = APIRouter(
    prefix="/companies/{company_id}/employees",
    tags=["Company employees (clients)"],
)


def _svc(db: DbSession) -> CompanyEmployeeService:
    return CompanyEmployeeService(db)


def _dump_emp(row) -> dict:
    return CompanyEmployeeRead.model_validate(row).model_dump(by_alias=True, mode="json")


def _dump_phone(row) -> dict:
    return CompanyEmployeePhoneRead.model_validate(row).model_dump(by_alias=True, mode="json")


def _dump_perm(row) -> dict:
    return EmployeeAppPermissionRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.post("", response_model=ApiResponse[CompanyEmployeeRead], summary="Create company employee")
def create_employee(
    company_id: UUID,
    data: CompanyEmployeeCreate,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        row = _svc(db).create_employee(str(company_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump_emp(row), message=ResponseEnum.SUCCESS.value)


@router.get("", response_model=ApiResponse[list[CompanyEmployeeRead]], summary="List my company employees")
def list_employees(company_id: UUID, db: DbSession, current: CurrentEmployerRequired):
    rows = _svc(db).list_employees_client(str(company_id), current)
    return json_success([_dump_emp(x) for x in rows], message=ResponseEnum.SUCCESS.value)


@router.get("/{employee_id}", response_model=ApiResponse[CompanyEmployeeRead], summary="Get company employee by id")
def get_employee(company_id: UUID, employee_id: UUID, db: DbSession, current: CurrentEmployerRequired):
    row = _svc(db).get_employee_client(str(company_id), str(employee_id), current)
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_emp(row), message=ResponseEnum.SUCCESS.value)


@router.patch("/{employee_id}", response_model=ApiResponse[CompanyEmployeeRead], summary="Update company employee")
def update_employee(
    company_id: UUID,
    employee_id: UUID,
    data: CompanyEmployeeUpdate,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        row = _svc(db).update_employee(str(company_id), str(employee_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_emp(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{employee_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Deactivate company employee",
)
def deactivate_employee(company_id: UUID, employee_id: UUID, db: DbSession, current: CurrentEmployerRequired):
    try:
        ok = _svc(db).deactivate_employee(str(company_id), str(employee_id), current)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Employee deactivated successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/{employee_id}/phones",
    response_model=ApiResponse[CompanyEmployeePhoneRead],
    summary="Add phone number to employee",
)
def add_employee_phone(
    company_id: UUID,
    employee_id: UUID,
    data: CompanyEmployeePhoneCreate,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        row = _svc(db).add_phone(str(company_id), str(employee_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump_phone(row), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{employee_id}/phones/{phone_id}",
    response_model=ApiResponse[CompanyEmployeePhoneRead],
    summary="Update employee phone number",
)
def update_employee_phone(
    company_id: UUID,
    employee_id: UUID,
    phone_id: UUID,
    data: CompanyEmployeePhoneUpdate,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        row = _svc(db).update_phone(str(company_id), str(employee_id), str(phone_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_phone(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{employee_id}/phones/{phone_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Deactivate employee phone number",
)
def deactivate_employee_phone(
    company_id: UUID,
    employee_id: UUID,
    phone_id: UUID,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        ok = _svc(db).deactivate_phone(str(company_id), str(employee_id), str(phone_id), current)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Phone deactivated successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{employee_id}/app-permissions",
    response_model=ApiResponse[list[EmployeeAppPermissionRead]],
    summary="Get employee app permissions",
)
def list_employee_app_permissions(company_id: UUID, employee_id: UUID, db: DbSession, current: CurrentEmployerRequired):
    rows = _svc(db).list_employee_app_permissions(str(company_id), str(employee_id), current, active_only=False)
    if rows is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success([_dump_perm(x) for x in rows], message=ResponseEnum.SUCCESS.value)
