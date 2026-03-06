"""Shared API dependencies (pagination params, etc.)."""

from typing import Annotated

from fastapi import Depends, Query

from app.common.pagination import PaginationParams


def get_pagination(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginationParams:
    """Extract pagination params from request."""
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(get_pagination)]
