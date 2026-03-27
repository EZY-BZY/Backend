"""
PostgreSQL connection service.

Purpose: primary relational data (SQLAlchemy ORM, Alembic migrations).
Use `get_db` / `DbSession` in FastAPI routes; engine is managed here.
"""

from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


class PostgresConnectionService:
    """Singleton-style SQLAlchemy engine and session factory for PostgreSQL."""

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.database_url.unicode_string()
        self._echo = settings.database_echo
        self._engine: Engine | None = None
        self._SessionLocal: sessionmaker[Session] | None = None

    def connect(self) -> None:
        """Create engine and session factory (idempotent)."""
        if self._engine is not None:
            return
        self._engine = create_engine(
            self._url,
            echo=self._echo,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            class_=Session,
            expire_on_commit=False,
        )

    def disconnect(self) -> None:
        """Dispose engine pool (call on app shutdown)."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._SessionLocal = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self.connect()
        assert self._engine is not None
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        if self._SessionLocal is None:
            self.connect()
        assert self._SessionLocal is not None
        return self._SessionLocal

    def health_check(self) -> bool:
        """Return True if PostgreSQL accepts a connection."""
        from sqlalchemy import text

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


@lru_cache
def get_postgres_service() -> PostgresConnectionService:
    """Cached Postgres connection service (one per process)."""
    svc = PostgresConnectionService()
    svc.connect()
    return svc


def get_db_session() -> Generator[Session, None, None]:
    """Yield a sync DB session. FastAPI dependency."""
    svc = get_postgres_service()
    session = svc.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Alias for get_db_session."""
    yield from get_db_session()


DbSession = Annotated[Session, Depends(get_db)]
