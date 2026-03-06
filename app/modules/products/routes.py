"""Product routes. Mount under /api/v1. Protect with company context + products permission."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.modules.products.dependencies import ProductServiceDep
from app.modules.products.schemas import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def _to_read(p) -> ProductRead:
    return ProductRead(
        id=UUID(p.id),
        company_id=UUID(p.company_id),
        name=p.name,
        sku=p.sku,
        description=p.description,
        unit_price=p.unit_price,
        currency=p.currency,
        is_active=p.is_active,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.post("", response_model=ProductRead)
def create_product(
    data: ProductCreate,
    service: ProductServiceDep,
    # In production: CurrentCompanyMember, require_permission("products:manage")
) -> ProductRead:
    """Create product. Requires company_id from auth context (placeholder)."""
    raise HTTPException(
        status_code=501,
        detail="Inject company_id from get_current_company_member",
    )


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: UUID, service: ProductServiceDep):
    """Get product by id (tenant-scoped)."""
    # Would pass current_member.company_id
    raise HTTPException(status_code=501, detail="Require company context")


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: UUID, data: ProductUpdate, service: ProductServiceDep):
    """Update product (tenant-scoped)."""
    raise HTTPException(status_code=501, detail="Require company context")
