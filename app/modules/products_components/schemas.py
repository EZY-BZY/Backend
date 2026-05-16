"""Pydantic schemas for products & components."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.products_components.models import Component, Product


def _strip_opt(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _strip_req(v: str) -> str:
    return str(v).strip()


class ComponentCreate(BaseModel):
    name_ar: str = Field(..., min_length=1, max_length=256)
    name_other: str = Field(..., min_length=1, max_length=256)
    description_ar: str | None = None
    description_other: str | None = None
    main_image: str | None = Field(None, max_length=2048)

    @field_validator("name_ar", "name_other", mode="before")
    @classmethod
    def _strip_names(cls, v: str) -> str:
        return _strip_req(v)

    @field_validator("description_ar", "description_other", "main_image", mode="before")
    @classmethod
    def _strip_optional(cls, v: str | None) -> str | None:
        return _strip_opt(v)


class ComponentUpdate(BaseModel):
    name_ar: str | None = Field(None, min_length=1, max_length=256)
    name_other: str | None = Field(None, min_length=1, max_length=256)
    description_ar: str | None = None
    description_other: str | None = None
    main_image: str | None = Field(None, max_length=2048)

    @field_validator("name_ar", "name_other", mode="before")
    @classmethod
    def _strip_names(cls, v: str | None) -> str | None:
        return _strip_opt(v) if v is not None else None

    @field_validator("description_ar", "description_other", "main_image", mode="before")
    @classmethod
    def _strip_optional(cls, v: str | None) -> str | None:
        return _strip_opt(v)


class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name_ar: str
    name_other: str
    description_ar: str | None
    description_other: str | None
    main_image: str | None
    created_by_type: str
    created_by_id: UUID
    updated_by_type: str | None
    updated_by_id: UUID | None
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    name_ar: str = Field(..., min_length=1, max_length=256)
    name_other: str = Field(..., min_length=1, max_length=256)
    description_ar: str | None = None
    description_other: str | None = None
    main_image: str | None = Field(None, max_length=2048)
    price: Decimal = Field(default=Decimal("0"), ge=0)
    show_price: bool = True
    show_product: bool = True

    @field_validator("name_ar", "name_other", mode="before")
    @classmethod
    def _strip_names(cls, v: str) -> str:
        return _strip_req(v)

    @field_validator("description_ar", "description_other", "main_image", mode="before")
    @classmethod
    def _strip_optional(cls, v: str | None) -> str | None:
        return _strip_opt(v)


class ProductUpdate(BaseModel):
    name_ar: str | None = Field(None, min_length=1, max_length=256)
    name_other: str | None = Field(None, min_length=1, max_length=256)
    description_ar: str | None = None
    description_other: str | None = None
    main_image: str | None = Field(None, max_length=2048)
    price: Decimal | None = Field(None, ge=0)
    show_price: bool | None = None
    show_product: bool | None = None

    @field_validator("name_ar", "name_other", mode="before")
    @classmethod
    def _strip_names(cls, v: str | None) -> str | None:
        return _strip_opt(v) if v is not None else None

    @field_validator("description_ar", "description_other", "main_image", mode="before")
    @classmethod
    def _strip_optional(cls, v: str | None) -> str | None:
        return _strip_opt(v)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name_ar: str
    name_other: str
    description_ar: str | None
    description_other: str | None
    main_image: str | None
    price: Decimal | None = None
    show_price: bool
    show_product: bool
    created_by_type: str
    created_by_id: UUID
    updated_by_type: str | None
    updated_by_id: UUID | None
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BranchQuantityCreate(BaseModel):
    branch_id: UUID
    quantity: Decimal = Field(..., ge=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def _coerce_quantity(cls, v: Any) -> Decimal:
        return Decimal(str(v))


class BranchQuantityUpdate(BaseModel):
    quantity: Decimal = Field(..., ge=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def _coerce_quantity(cls, v: Any) -> Decimal:
        return Decimal(str(v))


class ComponentBranchQuantityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    component_id: UUID
    branch_id: UUID
    quantity: Decimal
    created_at: datetime
    updated_at: datetime


class ProductBranchQuantityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    branch_id: UUID
    quantity: Decimal
    created_at: datetime
    updated_at: datetime


class ProductComponentCreate(BaseModel):
    component_id: UUID
    quantity: Decimal = Field(..., gt=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def _coerce_quantity(cls, v: Any) -> Decimal:
        return Decimal(str(v))


class ProductComponentUpdate(BaseModel):
    quantity: Decimal = Field(..., gt=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def _coerce_quantity(cls, v: Any) -> Decimal:
        return Decimal(str(v))


class ProductComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    component_id: UUID
    quantity: Decimal
    created_at: datetime
    updated_at: datetime


class ProductComponentWithComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    component_id: UUID
    quantity: Decimal
    component: ComponentRead
    created_at: datetime
    updated_at: datetime


class ProductDetailRead(BaseModel):
    product: dict[str, Any]
    quantities_per_branch: list[dict[str, Any]]
    components: list[dict[str, Any]]


def component_read_dict(row: Component) -> dict[str, Any]:
    return ComponentRead.model_validate(row).model_dump(mode="json")


def product_read_dict(row: Product, *, insider: bool = False) -> dict[str, Any]:
    """
    Serialize a product for API responses.

    - **insider** (company owner or company employee): all fields, including price.
    - **public**: omit price when ``show_price`` is false (products with ``show_product`` false
      should be excluded at query time).
    """
    d = ProductRead.model_validate(row).model_dump(mode="json")
    if not insider and not row.show_price:
        d["price"] = None
    return d
