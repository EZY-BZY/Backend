"""Public industries read routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import Pagination
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.allenums import ResponseEnum
from app.common.pagination import pagination_pages
from app.common.schemas import PaginatedResponse
from app.db.session import DbSession
from app.modules.industries.schemas import IndustryPublicRead
from app.modules.industries.service import IndustryService

router = APIRouter(prefix="/industries", tags=["Industries (public)"])


def _svc(db: DbSession) -> IndustryService:
    return IndustryService(db)


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[IndustryPublicRead]],
)
def list_industries(
    db: DbSession,
    pagination: Pagination,
):
    """Paginated list of industries (public)."""
    svc = _svc(db)
    items, total = svc.list_paginated(page=pagination.page, page_size=pagination.page_size)
    pages = pagination_pages(total, pagination.page_size)
    payload = PaginatedResponse(
        items=[IndustryPublicRead.model_validate(r) for r in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    ).model_dump()
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@router.get(
    "/{industry_id}",
    response_model=ApiResponse[IndustryPublicRead],
)
def get_industry(industry_id: UUID, db: DbSession):
    row = _svc(db).get_by_id(str(industry_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Industry not found")
    return json_success(
        IndustryPublicRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
