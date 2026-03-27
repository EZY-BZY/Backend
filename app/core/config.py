"""Environment-based settings. Loaded once at startup."""

import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="Supplier SaaS API", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api/v1")

    # Security
    secret_key: str = Field(default="change-me-in-production-min-32-chars-long")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    bcrypt_rounds: int = Field(default=12, ge=10, le=14)

    # PostgreSQL — relational data (ORM, migrations)
    database_url: PostgresDsn = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/supplier_saas"
    )
    database_echo: bool = Field(default=False, description="Echo SQL for debugging")

    # MongoDB — documents, flexible schemas, analytics payloads
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    mongodb_database: str = Field(
        default="supplier_saas",
        description="Default database name for MongoDB",
    )

    # Redis — cache, rate limits, pub/sub, queue readiness
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def _parse_list_from_env(cls, v: Any) -> Any:
        """
        Docker / shell often set CORS_ORIGINS as a plain string.
        Accept: JSON array, comma-separated list, or Python list.
        """
        if v is None or isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return v
            if s.startswith("["):
                try:
                    return json.loads(s)
                except json.JSONDecodeError:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
