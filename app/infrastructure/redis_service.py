"""
Redis connection service.

Purpose: caching, rate limiting, pub/sub, short-lived session data, job queue readiness.
Use `get_redis_client()` dependency or `get_redis_service().client` for raw access.
"""

from functools import lru_cache
from typing import Annotated

import redis
from fastapi import Depends

from app.core.config import get_settings


class RedisConnectionService:
    """Singleton Redis client with connection pool."""

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.redis_url
        self._client: redis.Redis | None = None

    def connect(self) -> None:
        """Create Redis client from URL (idempotent)."""
        if self._client is not None:
            return
        url_str = self._url.unicode_string()
        self._client = redis.from_url(
            url_str,
            decode_responses=True,
            socket_connect_timeout=5,
            health_check_interval=30,
        )

    def disconnect(self) -> None:
        """Close Redis connection pool."""
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self.connect()
        assert self._client is not None
        return self._client

    def health_check(self) -> bool:
        """Return True if Redis responds to PING."""
        try:
            return bool(self.client.ping())
        except Exception:
            return False


@lru_cache
def get_redis_service() -> RedisConnectionService:
    """Cached Redis connection service."""
    svc = RedisConnectionService()
    svc.connect()
    return svc


def get_redis_client() -> redis.Redis:
    """FastAPI dependency: Redis client (decode_responses=True)."""
    return get_redis_service().client


RedisClient = Annotated[redis.Redis, Depends(get_redis_client)]
