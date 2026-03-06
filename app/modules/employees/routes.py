"""Organization employees API: owner creation, members CRUD, org login. Owner excluded from list."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.common.pagination import pagination_pages
from app.common.schemas import MessageResponse, PaginatedResponse
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.modules.auth.schemas import TokenResponse
from app.modules.employees.dependencies import (
    CurrentEmployeeRequired,
    require_permission,
)
from app.modules.employees.schemas import (
    EmployeeRead,
    EmployeeReadWithPermissions,
    MemberCreate,
    MemberUpdate,
    OrgLoginRequest,
    OwnerCreate,
)
from app.modules.employees.service import EmployeeService
from app.db.session import DbSession
from app.modules.employees.enums import AccountStatus

router = APIRouter(prefix="/employees", tags=["organization-employees"])


def _get_service(db: DbSession) -> EmployeeService:
    return EmployeeService(db)


@router.post("/auth/login", response_model=TokenResponse)
def org_login(data: OrgLoginRequest, db: DbSession):
    """
    Organization login. Returns JWT with sub=employee_id.
    Use Authorization: Bearer <access_token> for protected endpoints.
    """
    service = _get_service(db)
    employee = service.get_by_email(data.email)
    if not employee or not verify_password(data.password, employee.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if employee.account_status != "active":
        raise HTTPException(status_code=403, detail="Account is inactive or suspended")
    if employee.deleted_at:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    settings = get_settings()
    access = create_access_token(employee.id)
    refresh = create_refresh_token(employee.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/owner",
    response_model=EmployeeRead,
    summary="Create organization owner",
    description="Creates the organization owner. Only one owner is allowed in the system. Rejects if owner already exists.",
)
def create_owner(
    data: OwnerCreate,
    db: DbSession,
):
    """
    Create organization owner. Callable only once in the system.
    Protected at service and DB: only one row with account_type='owner' allowed.
    """
    service = _get_service(db)
    try:
        owner = service.create_owner(data, created_by_id=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _employee_to_read(owner)


@router.post(
    "",
    response_model=EmployeeReadWithPermissions,
    dependencies=[Depends(require_permission("create_member"))],
)
def create_member(
    data: MemberCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Create a member (non-owner). Requires create_member permission."""
    service = _get_service(db)
    try:
        member = service.create_member(data, created_by_id=current.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    perm_names = service.get_permission_names(member.id)
    return _employee_to_read_with_perms(member, perm_names)


@router.get(
    "",
    response_model=PaginatedResponse[EmployeeReadWithPermissions],
    dependencies=[Depends(require_permission("view_members"))],
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
    List all members. Owner is always excluded from results.
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
    return PaginatedResponse(
        items=[_employee_to_read_with_perms(e, service.get_permission_names(e.id)) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeReadWithPermissions,
    dependencies=[Depends(require_permission("view_member"))],
)
def get_member(
    employee_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Get single member by id. Owner can be fetched by id but is excluded from list."""
    service = _get_service(db)
    employee = service.get_by_id(employee_id, include_deleted=False)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    perm_names = service.get_permission_names(employee.id)
    return _employee_to_read_with_perms(employee, perm_names)


@router.patch(
    "/{employee_id}",
    response_model=EmployeeReadWithPermissions,
    dependencies=[Depends(require_permission("update_member"))],
)
def update_member(
    employee_id: UUID,
    data: MemberUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Update member. Cannot convert to owner or update owner through this endpoint."""
    service = _get_service(db)
    try:
        employee = service.update_member(employee_id, data, updated_by_id=current.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    perm_names = service.get_permission_names(employee.id)
    return _employee_to_read_with_perms(employee, perm_names)


@router.delete(
    "/{employee_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("delete_member"))],
)
def deactivate_member(
    employee_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Soft-deactivate member (set deleted_at). Owner cannot be deactivated."""
    service = _get_service(db)
    try:
        employee = service.deactivate_member(employee_id, updated_by_id=current.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return MessageResponse(message="Member deactivated successfully")


def _employee_to_read(e) -> EmployeeRead:
    return EmployeeRead(
        id=UUID(e.id),
        full_name=e.full_name,
        email=e.email,
        phone=e.phone,
        account_type=e.account_type,
        account_status=e.account_status,
        created_at=e.created_at,
        updated_at=e.updated_at,
        created_by_id=UUID(e.created_by_id) if e.created_by_id else None,
        updated_by_id=UUID(e.updated_by_id) if e.updated_by_id else None,
    )


def _employee_to_read_with_perms(e, permission_names: list[str]) -> EmployeeReadWithPermissions:
    return EmployeeReadWithPermissions(
        **_employee_to_read(e).model_dump(),
        permission_names=permission_names,
    )
