"""Roles and permissions routes. Mount under /api/v1."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.modules.roles.dependencies import RoleServiceDep
from app.modules.roles.schemas import RoleRead

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/companies/{company_id}/roles", response_model=list[RoleRead])
def list_company_roles(company_id: UUID, service: RoleServiceDep):
    """List roles for a company (tenant). Require company context and roles:view or admin."""
    roles = service.list_roles_by_company(company_id)
    return [
        RoleRead(
            id=UUID(r.id),
            company_id=UUID(r.company_id),
            name=r.name,
            description=r.description,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in roles
    ]
