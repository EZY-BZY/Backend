"""
Infrastructure connections: PostgreSQL (relational), MongoDB (documents), Redis (cache/queue).

Import connection helpers from submodules:

    from app.infrastructure.postgres import get_postgres_service, get_db_session
    from app.infrastructure.mongo import get_mongo_service
    from app.infrastructure.redis_service import get_redis_service
"""

from app.infrastructure.postgres import (
    PostgresConnectionService,
    get_postgres_service,
    get_db_session,
    get_db,
    DbSession,
)
from app.infrastructure.redis_service import RedisConnectionService, get_redis_service
from app.infrastructure.mongo import MongoConnectionService, get_mongo_service

__all__ = [
    "PostgresConnectionService",
    "get_postgres_service",
    "get_db_session",
    "get_db",
    "DbSession",
    "RedisConnectionService",
    "get_redis_service",
    "MongoConnectionService",
    "get_mongo_service",
]
