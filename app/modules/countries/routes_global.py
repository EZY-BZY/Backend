"""Public countries read routes."""

from uuid import UUID

from fastapi import APIRouter
from app.common.api_response import json_error, json_success

from app.api.deps import Pagination
from app.common.api_response import ApiResponse
from app.common.allenums import ResponseEnum
from app.common.pagination import pagination_pages
from app.common.schemas import PaginatedResponse
from app.db.session import DbSession
from app.modules.countries.schemas import CountryPublicRead
from app.modules.countries.service import CountryService

router = APIRouter(prefix="/countries", tags=["Countries (public)"])


def _svc(db: DbSession) -> CountryService:
    return CountryService(db)


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[CountryPublicRead]],
)
def list_countries(
    db: DbSession,
    pagination: Pagination,
):
    """Public list of countries (paginated)."""
    svc = _svc(db)
    items, total = svc.list_paginated(page=pagination.page, page_size=pagination.page_size)
    pages = pagination_pages(total, pagination.page_size)
    payload = PaginatedResponse(
        items=[CountryPublicRead.model_validate(r) for r in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    ).model_dump()
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@router.get(
    "/{country_id}",
    response_model=ApiResponse[CountryPublicRead],
)
def get_country(country_id: UUID, db: DbSession):
    row = _svc(db).get_by_id(str(country_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Country not found")
    return json_success(
        CountryPublicRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )

