"""Uniform API envelope for every JSON response."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard response shape for the whole API.

    Keys match the product contract: status_code, Message, Data.
    """

    status_code: int = Field(..., description="Application status (typically matches HTTP status)")
    Message: str
    Data: T | None = None


def api_success(data: Any = None, *, message: str = "Success", status_code: int = 200) -> dict[str, Any]:
    """Build a success body (use when returning plain dict / JSONResponse)."""
    return {"status_code": status_code, "Message": message, "Data": data}


def api_error(
    message: str,
    *,
    status_code: int,
    data: Any = None,
) -> dict[str, Any]:
    """Build an error body (same keys as success; put details in Message and optional Data)."""
    return {"status_code": status_code, "Message": message, "Data": data}
