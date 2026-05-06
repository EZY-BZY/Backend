"""Uniform API envelope for every JSON response."""

from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
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
    return {"status_code": status_code, "Message": message, "details": data}


def json_success(
    data: Any = None,
    *,
    message: str = "Success",
    http_status: int = 200,
) -> JSONResponse:
    """
    Return a JSONResponse using the standard envelope.
    `http_status` is used for both HTTP status code and body.status_code.
    """
    return JSONResponse(
        status_code=http_status,
        content=jsonable_encoder(api_success(data, message=message, status_code=http_status)),
    )


def json_error(
    message: str,
    *,
    http_status: int,
    details: Any = None,
) -> JSONResponse:
    """
    Return a JSONResponse using the standard envelope.
    `http_status` is used for both HTTP status code and body.status_code.
    """
    return JSONResponse(
        status_code=http_status,
        content=jsonable_encoder(api_error(message, status_code=http_status, data=details)),
    )
