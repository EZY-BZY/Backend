"""Pagination and filtering utilities."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select


@dataclass
class PaginationParams:
    """Pagination parameters from request."""

    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def paginate_query(
    session: Any,
    query: Any,
    params: PaginationParams,
) -> tuple[list[Any], int]:
    """
    Execute a paginated query and return (items, total_count).
    Works with sync SQLAlchemy sessions.
    """
    # Count total (query should be a select)
    count_stmt = select(func.count()).select_from(query.subquery())
    total = session.execute(count_stmt).scalar_one()

    # Apply pagination
    paginated = query.offset(params.offset).limit(params.limit)
    items = list(session.execute(paginated).scalars().all())

    return items, total


def pagination_pages(total: int, page_size: int) -> int:
    """Compute total number of pages."""
    return max(0, (total + page_size - 1) // page_size) if page_size > 0 else 0
