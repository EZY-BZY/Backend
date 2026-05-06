"""Protected terms routes (Beasy employees only): CUD, admin list, audit history."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import Pagination
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.allenums import ResponseEnum
from app.common.pagination import pagination_pages
from app.common.schemas import MessageResponse, PaginatedResponse
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.terms.enums import TermType
from app.modules.terms.models import TermHistory
from app.modules.terms.schemas import (
    TermCreate,
    TermHistoryDayGroupRead,
    TermHistoryVersionRead,
    TermRead,
    TermUpdate,
)
from app.modules.terms.service import TermService

router = APIRouter(prefix="/terms", tags=["Terms (Beasy)"])


def _service(db: DbSession) -> TermService:
    return TermService(db)


def _history_row_to_read(row: TermHistory) -> TermHistoryVersionRead:
    return TermHistoryVersionRead.model_validate(row)


@router.post("", response_model=ApiResponse[TermRead])
def create_term(
    data: TermCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Create a term. `order` defaults to next position for this type if omitted."""
    svc = _service(db)
    try:
        term = svc.create(data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        TermRead.model_validate(term).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{term_type}/history",
    response_model=ApiResponse[PaginatedResponse[TermHistoryDayGroupRead]],
)
def list_term_history(
    term_type: TermType,
    db: DbSession,
    _: CurrentEmployeeRequired,
    pagination: Pagination,
):
    """
    Version history for this type only, paginated by UTC calendar day (newest first).
    Each day group lists change events that day (newest first), each with a full
    `terms_snapshot` for the type after that change.
    """
    svc = _service(db)
    groups_raw, total_days = svc.list_history_grouped_by_day(term_type, pagination)
    items: list[TermHistoryDayGroupRead] = []
    for day_start, rows in groups_raw:
        day_value = day_start.date() if isinstance(day_start, datetime) else day_start
        items.append(
            TermHistoryDayGroupRead(
                day=day_value,
                versions=[_history_row_to_read(r) for r in rows],
            )
        )
    pages = pagination_pages(total_days, pagination.page_size)
    return json_success(
        PaginatedResponse(
            items=items,
            total=total_days,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        ).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{term_type}",
    response_model=ApiResponse[list[TermRead]],
)
def list_terms_admin(
    term_type: TermType,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    """Full term rows for this type (ids, audit columns). Non-deleted only, ordered by `order`."""
    svc = _service(db)
    terms = svc.list_by_type_ordered(term_type, include_deleted=False)
    return json_success(
        [TermRead.model_validate(t).model_dump() for t in terms],
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch("/{term_id}", response_model=ApiResponse[TermRead])
def update_term(
    term_id: UUID,
    data: TermUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Update an active term. A version snapshot is stored automatically."""
    svc = _service(db)
    try:
        term = svc.update(str(term_id), data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details=str(e))
    return json_success(
        TermRead.model_validate(term).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete("/{term_id}", response_model=ApiResponse[MessageResponse])
def delete_term(
    term_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Soft-delete a term. A version snapshot is stored automatically."""
    svc = _service(db)
    try:
        svc.soft_delete(str(term_id), actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details=str(e))
    return json_success(
        MessageResponse(message="Term deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
