"""
FastAPI dependency shortcuts — import these in routes.

Example::

    from app.infrastructure.deps import DbSession, MongoDatabase, RedisClient

    @router.get("/example")
    def example(db: DbSession, mongo: MongoDatabase, cache: RedisClient):
        cache.set("k", "v", ex=60)
        mongo["events"].insert_one({"type": "ping"})
        return {"ok": True}
"""

from app.infrastructure.mongo import MongoDatabase
from app.infrastructure.postgres import DbSession
from app.infrastructure.redis_service import RedisClient

__all__ = ["DbSession", "MongoDatabase", "RedisClient"]
