"""Company routes. Mount under /api/v1/companies."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.common.schemas import MessageResponse
from app.modules.companies.dependencies import CompanyServiceDep
from app.modules.companies.schemas import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead)
def create_company(data: CompanyCreate, service: CompanyServiceDep) -> CompanyRead:
    """Create a new company (e.g. registration)."""
    # In real app you might check existing slug
    company = service.create(data)
    return CompanyRead(
        id=UUID(company.id),
        name=company.name,
        slug=company.slug,
        description=company.description,
        is_active=company.is_active,
        created_at=company.created_at.isoformat(),
        updated_at=company.updated_at.isoformat(),
    )


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: UUID, service: CompanyServiceDep):
    """Get company by id (public or admin)."""
    company = service.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyRead(
        id=UUID(company.id),
        name=company.name,
        slug=company.slug,
        description=company.description,
        is_active=company.is_active,
        created_at=company.created_at.isoformat(),
        updated_at=company.updated_at.isoformat(),
    )


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: UUID, data: CompanyUpdate, service: CompanyServiceDep):
    """Update company (tenant admin only - guard in real app)."""
    company = service.update(company_id, data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyRead(
        id=UUID(company.id),
        name=company.name,
        slug=company.slug,
        description=company.description,
        is_active=company.is_active,
        created_at=company.created_at.isoformat(),
        updated_at=company.updated_at.isoformat(),
    )
