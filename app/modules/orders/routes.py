"""Order routes. Mount under /api/v1. Protect with company context + orders permission."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.modules.orders.dependencies import OrderServiceDep
from app.modules.orders.schemas import OrderCreate, OrderRead, OrderItemRead

router = APIRouter(prefix="/orders", tags=["orders"])


def _item_to_read(i) -> OrderItemRead:
    return OrderItemRead(
        id=UUID(i.id),
        order_id=UUID(i.order_id),
        product_id=UUID(i.product_id) if i.product_id else None,
        description=i.description,
        quantity=i.quantity,
        unit_price=i.unit_price,
        currency=i.currency,
        created_at=i.created_at.isoformat(),
        updated_at=i.updated_at.isoformat(),
    )


@router.post("", response_model=OrderRead)
def create_order(
    data: OrderCreate,
    service: OrderServiceDep,
    # current_member: CurrentCompanyMember, require_permission("orders:manage")
):
    """Create order. In production inject buyer_company_id and user from auth."""
    raise HTTPException(status_code=501, detail="Require company and user context")


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: UUID, service: OrderServiceDep):
    """Get order by id (buyer company only)."""
    order = service.get_by_id(order_id, "00000000-0000-0000-0000-000000000000")
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead(
        id=UUID(order.id),
        buyer_company_id=UUID(order.buyer_company_id),
        seller_company_id=UUID(order.seller_company_id),
        created_by_user_id=UUID(order.created_by_user_id) if order.created_by_user_id else None,
        status=order.status,
        reference=order.reference,
        note=order.note,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
        items=[_item_to_read(i) for i in order.items],
    )
