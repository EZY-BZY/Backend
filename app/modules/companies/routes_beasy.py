"""Beasy: list all companies (read-only)."""

from __future__ import annotations

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.companies.schemas import CompanyRead
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
    items = _svc(db).list_companies()
    return json_success(
        [CompanyRead.model_validate(c).model_dump() for c in items],
        message=ResponseEnum.SUCCESS.value,
    )
