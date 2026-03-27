"""
MongoDB connection service.

Purpose: document-oriented data (flexible schemas, logs, analytics payloads, feature flags).
Use `get_mongo_database()` or `get_mongo_collection("name")` from dependencies.
"""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.config import get_settings


class MongoConnectionService:
    """Manages a single MongoClient and default database."""

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.mongodb_url
        self._db_name = settings.mongodb_database
        self._client: MongoClient[Any] | None = None

    def connect(self) -> None:
        """Create MongoClient (idempotent)."""
        if self._client is not None:
            return
        self._client = MongoClient(
            self._url,
            serverSelectionTimeoutMS=5000,
        )

    def disconnect(self) -> None:
        """Close MongoClient."""
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> MongoClient[Any]:
        if self._client is None:
            self.connect()
        assert self._client is not None
        return self._client

    def get_database(self, name: str | None = None) -> Database[Any]:
        """Return a database; defaults to configured MONGODB_DATABASE."""
        db_name = name or self._db_name
        return self.client[db_name]

    def get_collection(self, collection: str, db_name: str | None = None) -> Collection[Any]:
        """Return a collection from the default or named database."""
        return self.get_database(db_name)[collection]

    def health_check(self) -> bool:
        """Return True if MongoDB responds to ping."""
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False


@lru_cache
def get_mongo_service() -> MongoConnectionService:
    """Cached MongoDB connection service."""
    svc = MongoConnectionService()
    svc.connect()
    return svc


def get_mongo_database() -> Database[Any]:
    """FastAPI dependency: default MongoDB database."""
    return get_mongo_service().get_database()


def get_mongo_collection(collection_name: str):
    """Factory for a FastAPI dependency that returns a named collection."""

    def _dep() -> Collection[Any]:
        return get_mongo_service().get_collection(collection_name)

    return _dep


MongoDatabase = Annotated[Database[Any], Depends(get_mongo_database)]
