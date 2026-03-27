"""Database session factory and dependency (PostgreSQL via infrastructure layer)."""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.postgres import (
    DbSession,
    get_db,
    get_db_session,
    get_postgres_service,
)


def __getattr__(name: str):
    """
    Lazy engine / SessionLocal so importing this module does not eagerly build
    the SQLAlchemy engine (helps isolate import errors from uvicorn's async stack).
    """
    if name == "engine":
        return get_postgres_service().engine
    if name == "SessionLocal":
        return get_postgres_service().session_factory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "engine",
    "SessionLocal",
    "get_db_session",
    "get_db",
    "DbSession",
]
