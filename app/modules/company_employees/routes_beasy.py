"""
Beasy — **company employees** (read / filter).

**Base path:** ``/beasy/company-employees``

**Auth:** Beasy employee JWT.

**Filters:** optional ``company_id``, ``role``, ``department``, ``is_active``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.common.allenums import CompanyEmployeeRole, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.company_employees.schemas import CompanyEmployeeBeasyRead
from app.modules.company_employees.service import CompanyEmployeeService

router = APIRouter(
    prefix="/company-employees",
    tags=["Company employees (Beasy)"],
)


def _svc(db: DbSession) -> CompanyEmployeeService:
    return CompanyEmployeeService(db)


def _dump(row) -> dict:
    return CompanyEmployeeBeasyRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[CompanyEmployeeBeasyRead]],
    summary="List company employees (filterable)",
)
def list_company_employees(
    db: DbSession,
    _: CurrentEmployeeRequired,
    company_id: UUID | None = Query(None),
    role: CompanyEmployeeRole | None = Query(None),
    department: str | None = Query(None, max_length=256),
    is_active: bool | None = Query(None, description="Filter by employee active flag"),
):
    rows = _svc(db).list_employees_beasy(
        company_id=str(company_id) if company_id is not None else None,
        role=role.value if role is not None else None,
        department=department,
        is_active=is_active,
    )
    return json_success([_dump(x) for x in rows], message=ResponseEnum.SUCCESS.value)


@router.get(
    "/{employee_id}",
    response_model=ApiResponse[CompanyEmployeeBeasyRead],
    summary="Get company employee by id",
)
def get_company_employee(employee_id: UUID, db: DbSession, _: CurrentEmployeeRequired):
    row = _svc(db).get_employee_beasy(str(employee_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)
