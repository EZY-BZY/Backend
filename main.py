"""
Supplier SaaS backend - modular monolith.
Run with: uvicorn main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.api.v1 import api_router

# Ensure all models are loaded for Alembic/DB
import app.db.models_registry  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    setup_logging()
    yield
    # Teardown: close pools, etc. if needed


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Multi-tenant SaaS backend for suppliers",
        version="0.1.0",
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

    @app.get("/health")
    def health():
        """Health check for load balancers and containers."""
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
