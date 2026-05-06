"""Centralized exception classes and handlers."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.api_response import api_error
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        elif isinstance(detail, list | dict):
            message = str(detail)
        else:
            message = str(detail)
        code = int(exc.status_code)
        return JSONResponse(
            status_code=code,
            content=api_error(message, status_code=code, data=None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        logger.warning("Validation error on %s: %s", request.url.path, errors)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return JSONResponse(
            status_code=code,
            content=api_error(
                "Validation error",
                status_code=code,
                data=errors,
            ),
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("App error: %s", exc.message)
        code = int(exc.status_code)
        return JSONResponse(
            status_code=code,
            content=api_error(exc.message, status_code=code, data=None),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            status_code=code,
            content=api_error("General Internal server error", status_code=code, data=None),
        )
