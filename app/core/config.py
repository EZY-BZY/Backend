"""Environment-based settings. Loaded once at startup."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
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

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/supplier_saas"
    )
    database_echo: bool = Field(default=False, description="Echo SQL for debugging")

    # Redis
    redis_url: RedisDsn | None = Field(default=None)

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
