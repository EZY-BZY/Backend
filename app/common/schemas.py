"""Reusable Pydantic schemas for API responses (pagination, errors, etc.)."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""

    items: list[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=0, description="Total pages")


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    detail: str | None = None


class ErrorDetail(BaseModel):
    """Error detail for validation/API errors."""

    loc: list[str] | None = None
    msg: str
    type: str | None = None
