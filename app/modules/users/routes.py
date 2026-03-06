"""User (employee) routes. Mount under /api/v1. Protect with get_current_company_member."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.common.pagination import PaginationParams, paginate_query, pagination_pages
from app.common.schemas import PaginatedResponse
from app.modules.users.dependencies import UserServiceDep
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def create_user(
    data: UserCreate,
    service: UserServiceDep,
    # In real app: current_member: CurrentCompanyMemberDep
    # For boilerplate we'd inject company_id from auth context
) -> UserRead:
    """Create employee in current company (admin only)."""
    # Placeholder: require company_id from auth; for demo we skip
    raise HTTPException(
        status_code=501,
        detail="Use auth context to get company_id and require permission users:manage",
    )


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, service: UserServiceDep):
    """Get user by id (same company only)."""
    user = service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_read(user)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, data: UserUpdate, service: UserServiceDep):
    """Update user (same company, appropriate permission)."""
    # Would use current_member.company_id
    raise HTTPException(status_code=501, detail="Require company context from auth")


def _user_to_read(user) -> UserRead:
    return UserRead(
        id=UUID(user.id),
        company_id=UUID(user.company_id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_blocked=user.is_blocked,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )
