"""Public industries read routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import Pagination
from app.common.api_response import ApiResponse
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
    return ApiResponse(
        status_code=200,
        Message="Success",
        Data=PaginatedResponse(
            items=[IndustryPublicRead.model_validate(r) for r in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        ),
    )


@router.get(
    "/{industry_id}",
    response_model=ApiResponse[IndustryPublicRead],
)
def get_industry(industry_id: UUID, db: DbSession):
    row = _svc(db).get_by_id(str(industry_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Industry not found")
    return ApiResponse(
        status_code=200,
        Message="Success",
        Data=IndustryPublicRead.model_validate(row),
    )
