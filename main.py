"""
Supplier SaaS backend - modular monolith.
Run with: uvicorn main:app --reload
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.common.api_response import ApiResponse, api_success
from app.common.allenums import ResponseEnum

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.api.v1 import api_router
from app.infrastructure.mongo import get_mongo_service
from app.infrastructure.postgres import get_postgres_service
from app.infrastructure.redis_service import get_redis_service

# Ensure all models are loaded for Alembic/DB
import app.db.models_registry  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown hooks.
    We do not open DB/Redis/Mongo here so the server can bind :8000 even if a
    dependency is briefly unavailable (Docker race). Connections are lazy on first use.
    """
    setup_logging()
    yield
    for svc, clear in (
        (get_postgres_service, get_postgres_service.cache_clear),
        (get_mongo_service, get_mongo_service.cache_clear),
        (get_redis_service, get_redis_service.cache_clear),
    ):
        try:
            svc().disconnect()
        except Exception:
            pass
        try:
            clear()
        except Exception:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=f"B-easy Multi-tenant SaaS backend v{settings.version}",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    setup_middleware(app)
    setup_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    assets_root: Path = settings.media_assets_path
    assets_root.mkdir(parents=True, exist_ok=True)
    for sub in ("images", "videos", "files"):
        (assets_root / sub).mkdir(parents=True, exist_ok=True)
    app.mount(
        f"{settings.api_v1_prefix}/assets",
        StaticFiles(directory=str(assets_root)),
        name="assets",
    )

    @app.get("/health", response_model=ApiResponse[dict])
    def health():
        """Health check for load balancers and containers."""
        return ApiResponse(
            status_code=200,
            Message=ResponseEnum.SUCCESS.value,
            Data={"App Name": settings.app_name},
        )

    @app.get("/health/ready")
    def health_ready():
        """Readiness: PostgreSQL, MongoDB, Redis connectivity."""
        pg = get_postgres_service().health_check()
        mongo = get_mongo_service().health_check()
        redis_ok = get_redis_service().health_check()
        ok = pg and mongo and redis_ok
        http = 200 if ok else 503
        body = api_success(
            {
                "status": "ready" if ok else "degraded",
                "postgresql": "up" if pg else "down",
                "mongodb": "up" if mongo else "down",
                "redis": "up" if redis_ok else "down",
            },
            message="ready" if ok else "degraded",
            status_code=http,
        )
        return JSONResponse(status_code=http, content=body)

    return app


app = create_app()
