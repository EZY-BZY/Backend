"""
Beasy — list and inspect **company branches** across companies.

**Base path:** ``/beasy/company-branches``

**Auth:** Beasy employee JWT.

**Filters:** optional ``company_id``, ``branch_type``, ``is_active`` query parameters.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.common.allenums import CompanyBranchType, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.company_branches.schemas import CompanyBranchBeasyRead
from app.modules.company_branches.service import CompanyBranchService

router = APIRouter(
    prefix="/company-branches",
    tags=["Company branches (Beasy)"],
)


def _svc(db: DbSession) -> CompanyBranchService:
    return CompanyBranchService(db)


def _dump(row) -> dict:
    return CompanyBranchBeasyRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[CompanyBranchBeasyRead]],
    summary="List company branches (filterable)",
)
def list_company_branches(
    db: DbSession,
    _: CurrentEmployeeRequired,
    company_id: UUID | None = Query(None, description="Filter by company"),
    branch_type: CompanyBranchType | None = Query(None, description="Filter by branch type"),
    is_active: bool | None = Query(None, description="Filter by branch active flag"),
):
    rows = _svc(db).list_branches_beasy(
        company_id=str(company_id) if company_id is not None else None,
        branch_type=branch_type.value if branch_type is not None else None,
        is_active=is_active,
    )
    return json_success(
        [_dump(x) for x in rows],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{branch_id}",
    response_model=ApiResponse[CompanyBranchBeasyRead],
    summary="Get company branch by id",
)
def get_company_branch(branch_id: UUID, db: DbSession, _: CurrentEmployeeRequired):
    row = _svc(db).get_branch_beasy(str(branch_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)
