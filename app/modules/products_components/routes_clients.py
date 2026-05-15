"""
Clients — **products & components** for one company.

**Base paths**

- ``/clients/companies/{company_id}/components``
- ``/clients/companies/{company_id}/products``

**Auth:** Client JWT (``account_type`` owner or company_employee). Employees need ``company_id`` in the token
matching the path company.

**Images:** JSON body may include ``main_image`` URL, or send ``multipart/form-data`` with optional
``main_image`` file (validated via shared upload rules).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.api.deps import Pagination
from app.common.pagination import pagination_pages
from app.common.schemas import PaginatedResponse
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentClientRequired, OptionalCurrentClient
from app.modules.products_components.schemas import (
    BranchQuantityCreate,
    BranchQuantityUpdate,
    ComponentBranchQuantityRead,
    ComponentCreate,
    ComponentRead,
    ComponentUpdate,
    ProductBranchQuantityRead,
    ProductComponentCreate,
    ProductComponentRead,
    ProductComponentUpdate,
    ProductComponentWithComponentRead,
    ProductCreate,
    ProductDetailRead,
    ProductRead,
    ProductUpdate,
    component_read_dict,
    product_read_dict,
)
from app.modules.products_components.service import ProductsComponentsService
from app.modules.products_components.upload_helpers import resolve_main_image, validate_main_image_url

router = APIRouter(tags=["Products & components (clients)"])

components_router = APIRouter(prefix="/companies/{company_id}/components")
products_router = APIRouter(prefix="/companies/{company_id}/products")


def _svc(db: DbSession) -> ProductsComponentsService:
    return ProductsComponentsService(db)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


@components_router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[ComponentRead]],
    summary="List components for the company (paginated)",
    description=(
        "Paginated list of active components. Requires company owner or company employee JWT "
        "for this ``company_id``. Query: ``page`` (default 1), ``page_size`` (default 20, max 100)."
    ),
)
def list_components(
    company_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    pagination: Pagination,
):
    result = _svc(db).list_components_paginated(
        str(company_id),
        current,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    if result is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    rows, total = result
    pages = pagination_pages(total, pagination.page_size)
    payload = PaginatedResponse(
        items=[component_read_dict(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    ).model_dump(mode="json")
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@components_router.post(
    "",
    response_model=ApiResponse[ComponentRead],
    summary="Create component",
)
def create_component(
    company_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: ComponentCreate,
):
    try:
        validate_main_image_url(data.main_image)
        row = _svc(db).create_component(str(company_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(component_read_dict(row), message=ResponseEnum.SUCCESS.value)


@components_router.get(
    "/{component_id}",
    response_model=ApiResponse[ComponentRead],
    summary="Get component by id",
)
def get_component(
    company_id: UUID,
    component_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    row = _svc(db).get_component(str(company_id), str(component_id), current)
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Component not found")
    return json_success(component_read_dict(row), message=ResponseEnum.SUCCESS.value)


@components_router.patch(
    "/{component_id}",
    response_model=ApiResponse[ComponentRead],
    summary="Update component",
)
def update_component(
    company_id: UUID,
    component_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: ComponentUpdate,
):
    try:
        validate_main_image_url(data.main_image)
        row = _svc(db).update_component(str(company_id), str(component_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Component not found")
    return json_success(component_read_dict(row), message=ResponseEnum.SUCCESS.value)


@components_router.post(
    "/{component_id}/main-image",
    response_model=ApiResponse[ComponentRead],
    summary="Upload component main image",
    description="``multipart/form-data`` with one image file (jpg, jpeg, png, webp per project settings).",
)
async def upload_component_main_image(
    company_id: UUID,
    component_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    main_image: UploadFile = File(...),
):
    try:
        image_url = await resolve_main_image(upload=main_image, url=None)
        row = _svc(db).update_component(
            str(company_id),
            str(component_id),
            current,
            ComponentUpdate(),
            main_image_url=image_url,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Component not found")
    return json_success(component_read_dict(row), message=ResponseEnum.SUCCESS.value)


@components_router.delete(
    "/{component_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete component (soft)",
    description="Sets ``is_active`` to false.",
)
def delete_component(
    company_id: UUID,
    component_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    ok = _svc(db).delete_component(str(company_id), str(component_id), current)
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Component not found")
    return json_success(
        MessageResponse(message="Component deactivated").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


# --- Component branch quantities ---


@components_router.get(
    "/{component_id}/branch-quantities",
    response_model=ApiResponse[list[ComponentBranchQuantityRead]],
    summary="List component quantities per branch",
)
def list_component_branch_quantities(
    company_id: UUID,
    component_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    rows = _svc(db).list_component_branch_quantities(str(company_id), str(component_id), current)
    if rows is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Component not found")
    return json_success(
        [ComponentBranchQuantityRead.model_validate(r).model_dump(mode="json") for r in rows],
        message=ResponseEnum.SUCCESS.value,
    )


@components_router.post(
    "/{component_id}/branch-quantities",
    response_model=ApiResponse[ComponentBranchQuantityRead],
    summary="Create component quantity for a branch",
)
def create_component_branch_quantity(
    company_id: UUID,
    component_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: BranchQuantityCreate,
):
    try:
        row = _svc(db).create_component_branch_quantity(
            str(company_id),
            str(component_id),
            current,
            data,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        ComponentBranchQuantityRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@components_router.patch(
    "/{component_id}/branch-quantities/{quantity_id}",
    response_model=ApiResponse[ComponentBranchQuantityRead],
    summary="Update component branch quantity",
)
def update_component_branch_quantity(
    company_id: UUID,
    component_id: UUID,
    quantity_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: BranchQuantityUpdate,
):
    try:
        row = _svc(db).update_component_branch_quantity(
            str(company_id),
            str(component_id),
            str(quantity_id),
            current,
            data,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Quantity record not found")
    return json_success(
        ComponentBranchQuantityRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@components_router.delete(
    "/{component_id}/branch-quantities/{quantity_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete component branch quantity",
)
def delete_component_branch_quantity(
    company_id: UUID,
    component_id: UUID,
    quantity_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    ok = _svc(db).delete_component_branch_quantity(
        str(company_id),
        str(component_id),
        str(quantity_id),
        current,
    )
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Quantity record not found")
    return json_success(
        MessageResponse(message="Quantity record deleted").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


@products_router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[ProductRead]],
    summary="List products for the company (paginated)",
    description=(
        "Paginated list of active products for the company.\n\n"
        "**Company owner or company employee** (valid JWT for this ``company_id``): "
        "all active products, including those with ``show_product=false``; prices always visible.\n\n"
        "**Everyone else** (no token, invalid token, or unrelated user): only products with "
        "``show_product=true``; ``price`` is omitted when ``show_price=false``."
    ),
)
def list_products(
    company_id: UUID,
    db: DbSession,
    pagination: Pagination,
    current: OptionalCurrentClient = None,
):
    result = _svc(db).list_products_paginated(
        str(company_id),
        current,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    if result is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    rows, total, insider = result
    pages = pagination_pages(total, pagination.page_size)
    payload = PaginatedResponse(
        items=[product_read_dict(r, insider=insider) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    ).model_dump(mode="json")
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@products_router.post(
    "",
    response_model=ApiResponse[ProductRead],
    summary="Create product",
)
def create_product(
    company_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: ProductCreate,
):
    try:
        validate_main_image_url(data.main_image)
        row = _svc(db).create_product(str(company_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(product_read_dict(row, insider=True), message=ResponseEnum.SUCCESS.value)


@products_router.get(
    "/{product_id}",
    response_model=ApiResponse[ProductDetailRead],
    summary="Get product details",
    description=(
        "Returns product fields, ``quantities_per_branch``, and ``components`` "
        "(each with nested component data and required quantity)."
    ),
)
def get_product_detail(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    detail = _svc(db).get_product_detail(str(company_id), str(product_id), current)
    if detail is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product not found")
    return json_success(detail, message=ResponseEnum.SUCCESS.value)


@products_router.patch(
    "/{product_id}",
    response_model=ApiResponse[ProductRead],
    summary="Update product",
)
def update_product(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: ProductUpdate,
):
    try:
        validate_main_image_url(data.main_image)
        row = _svc(db).update_product(str(company_id), str(product_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product not found")
    return json_success(product_read_dict(row, insider=True), message=ResponseEnum.SUCCESS.value)


@products_router.post(
    "/{product_id}/main-image",
    response_model=ApiResponse[ProductRead],
    summary="Upload product main image",
)
async def upload_product_main_image(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    main_image: UploadFile = File(...),
):
    try:
        image_url = await resolve_main_image(upload=main_image, url=None)
        row = _svc(db).update_product(
            str(company_id),
            str(product_id),
            current,
            ProductUpdate(),
            main_image_url=image_url,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product not found")
    return json_success(product_read_dict(row, insider=True), message=ResponseEnum.SUCCESS.value)


@products_router.delete(
    "/{product_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete product (soft)",
)
def delete_product(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    ok = _svc(db).delete_product(str(company_id), str(product_id), current)
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product not found")
    return json_success(
        MessageResponse(message="Product deactivated").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


# --- Product branch quantities ---


@products_router.get(
    "/{product_id}/branch-quantities",
    response_model=ApiResponse[list[ProductBranchQuantityRead]],
    summary="List product quantities per branch",
)
def list_product_branch_quantities(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    rows = _svc(db).list_product_branch_quantities(str(company_id), str(product_id), current)
    if rows is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product not found")
    return json_success(
        [ProductBranchQuantityRead.model_validate(r).model_dump(mode="json") for r in rows],
        message=ResponseEnum.SUCCESS.value,
    )


@products_router.post(
    "/{product_id}/branch-quantities",
    response_model=ApiResponse[ProductBranchQuantityRead],
    summary="Create product quantity for a branch",
)
def create_product_branch_quantity(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: BranchQuantityCreate,
):
    try:
        row = _svc(db).create_product_branch_quantity(
            str(company_id),
            str(product_id),
            current,
            data,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        ProductBranchQuantityRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@products_router.patch(
    "/{product_id}/branch-quantities/{quantity_id}",
    response_model=ApiResponse[ProductBranchQuantityRead],
    summary="Update product branch quantity",
)
def update_product_branch_quantity(
    company_id: UUID,
    product_id: UUID,
    quantity_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: BranchQuantityUpdate,
):
    try:
        row = _svc(db).update_product_branch_quantity(
            str(company_id),
            str(product_id),
            str(quantity_id),
            current,
            data,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Quantity record not found")
    return json_success(
        ProductBranchQuantityRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@products_router.delete(
    "/{product_id}/branch-quantities/{quantity_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete product branch quantity",
)
def delete_product_branch_quantity(
    company_id: UUID,
    product_id: UUID,
    quantity_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    ok = _svc(db).delete_product_branch_quantity(
        str(company_id),
        str(product_id),
        str(quantity_id),
        current,
    )
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Quantity record not found")
    return json_success(
        MessageResponse(message="Quantity record deleted").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


# --- Product components ---


@products_router.get(
    "/{product_id}/components",
    response_model=ApiResponse[list[ProductComponentWithComponentRead]],
    summary="List components used by a product",
)
def list_product_components(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    rows = _svc(db).list_product_components(str(company_id), str(product_id), current)
    if rows is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product not found")
    payload = []
    for link in rows:
        if link.component is None:
            continue
        payload.append(
            ProductComponentWithComponentRead(
                id=link.id,
                product_id=link.product_id,
                component_id=link.component_id,
                quantity=link.quantity,
                component=link.component,
                created_at=link.created_at,
                updated_at=link.updated_at,
            ).model_dump(mode="json")
        )
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@products_router.post(
    "/{product_id}/components",
    response_model=ApiResponse[ProductComponentWithComponentRead],
    summary="Add component to product",
)
def add_product_component(
    company_id: UUID,
    product_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: ProductComponentCreate,
):
    try:
        link = _svc(db).add_product_component(str(company_id), str(product_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if link.component is None:
        return json_error(ResponseEnum.ERROR.value, http_status=500, details="Component could not be loaded")
    return json_success(
        ProductComponentWithComponentRead(
            id=link.id,
            product_id=link.product_id,
            component_id=link.component_id,
            quantity=link.quantity,
            component=link.component,
            created_at=link.created_at,
            updated_at=link.updated_at,
        ).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@products_router.patch(
    "/{product_id}/components/{link_id}",
    response_model=ApiResponse[ProductComponentRead],
    summary="Update component quantity inside product",
)
def update_product_component(
    company_id: UUID,
    product_id: UUID,
    link_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
    data: ProductComponentUpdate,
):
    try:
        row = _svc(db).update_product_component(
            str(company_id),
            str(product_id),
            str(link_id),
            current,
            data,
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product component link not found")
    return json_success(
        ProductComponentRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@products_router.delete(
    "/{product_id}/components/{link_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Remove component from product",
)
def delete_product_component(
    company_id: UUID,
    product_id: UUID,
    link_id: UUID,
    db: DbSession,
    current: CurrentClientRequired,
):
    ok = _svc(db).delete_product_component(
        str(company_id),
        str(product_id),
        str(link_id),
        current,
    )
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Product component link not found")
    return json_success(
        MessageResponse(message="Component removed from product").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


router.include_router(components_router)
router.include_router(products_router)
