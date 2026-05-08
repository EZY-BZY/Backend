"""Beasy: list all companies (read-only)."""

from __future__ import annotations

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.companies.schemas import CompanyRead, company_read_dict
from app.modules.companies.service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies (Beasy)"])


def _svc(db: DbSession) -> CompanyService:
    return CompanyService(db)


@router.get(
    "",
    response_model=ApiResponse[list[CompanyRead]],
    summary="List all companies",
    description="Returns every company profile in the system, newest first.",
)
def list_companies(db: DbSession, _: CurrentEmployeeRequired):
    svc = _svc(db)
    items = svc.list_companies()
    by_c = svc.industry_ids_by_company_ids([str(c.id) for c in items])
    return json_success(
        [company_read_dict(c, by_c.get(str(c.id), [])) for c in items],
        message=ResponseEnum.SUCCESS.value,
    )
