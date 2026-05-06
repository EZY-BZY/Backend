"""Beasy employees API: Super User creation, members CRUD. Use `beasy_auth` for dashboard login."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.common.api_response import ApiResponse, json_error, json_success
from app.common.allenums import ResponseEnum
from app.common.pagination import pagination_pages
from app.common.schemas import MessageResponse, PaginatedResponse
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.beasy_employees.schemas import (
    EmployeeRead,
    MemberCreate,
    MemberUpdate,
    OwnerCreate,
)
from app.modules.beasy_employees.service import EmployeeService
from app.db.session import DbSession
from app.common.allenums import AccountStatus

router = APIRouter(prefix="/employees", tags=["Employees (Beasy)"])


def _get_service(db: DbSession) -> EmployeeService:
    return EmployeeService(db)


@router.post(
    "/super-user",
    response_model=ApiResponse[EmployeeRead],
    summary="Create B-easy Super User",
    description="Creates the B-easy Super User. Only one Super User is allowed in the system. Rejects if Super User already exists.",
)
def create_super_user_route(
    data: OwnerCreate,
    db: DbSession,
):
    """Create B-easy Super User. Callable only once in the system."""
    service = _get_service(db)
    try:
        owner = service.create_super_user(data, created_by_id=None)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        _employee_to_read(owner).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "",
    response_model=ApiResponse[EmployeeRead],
)
def create_member(
    data: MemberCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Create a member (non–Super User). Requires authentication."""
    service = _get_service(db)
    try:
        member = service.create_member(data, created_by_id=current.id)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        _employee_to_read(member).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[EmployeeRead]],
)
def list_members(
    db: DbSession,
    current: CurrentEmployeeRequired,
    account_status: AccountStatus | None = Query(None, description="Filter by status"),
    name: str | None = Query(None, description="Search in full name"),
    email: str | None = Query(None),
    phone: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all members. Super User is always excluded from results.
    Filter by account_status, name, email, phone. Sorted newest first.
    """
    service = _get_service(db)
    items, total = service.list_members(
        account_status=account_status.value if account_status else None,
        name=name,
        email=email,
        phone=phone,
        page=page,
        page_size=page_size,
    )
    pages = pagination_pages(total, page_size)
    return json_success(
        PaginatedResponse(
            items=[_employee_to_read(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{employee_id}",
    response_model=ApiResponse[EmployeeRead],
)
def get_member(
    employee_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Get single member by id. Super User can be fetched by id but is excluded from list."""
    service = _get_service(db)
    employee = service.get_by_id(employee_id, include_deleted=False)
    if not employee:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Employee not found")
    return json_success(_employee_to_read(employee).model_dump(), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{employee_id}",
    response_model=ApiResponse[EmployeeRead],
)
def update_member(
    employee_id: UUID,
    data: MemberUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Update member. Cannot convert to Super User or update Super User through this endpoint."""
    service = _get_service(db)
    try:
        employee = service.update_member(employee_id, data, updated_by_id=current.id)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not employee:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Employee not found")
    return json_success(
        _employee_to_read(employee).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete(
    "/{employee_id}",
    response_model=ApiResponse[MessageResponse],
)
def deactivate_member(
    employee_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Soft-deactivate member (set deleted_at). Super User cannot be deactivated."""
    service = _get_service(db)
    try:
        employee = service.deactivate_member(employee_id, updated_by_id=current.id)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not employee:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Employee not found")
    return json_success(
        MessageResponse(message="Member deactivated successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


def _employee_to_read(e) -> EmployeeRead:
    return EmployeeRead(
        id=UUID(e.id),
        name=e.name,
        email=e.email,
        phone=e.phone,
        account_type=e.account_type,
        account_status=e.account_status,
        created_at=e.created_at,
        updated_at=e.updated_at,
        created_by_id=UUID(e.created_by_id) if e.created_by_id else None,
        updated_by_id=UUID(e.updated_by_id) if e.updated_by_id else None,
    )
