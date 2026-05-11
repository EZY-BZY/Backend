"""Environment-based settings. Loaded once at startup."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, PostgresDsn, RedisDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # App
    app_name: str = Field(default="B-easy SaaS API Default Value", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="production"
    )
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api/v1")

    # Security
    secret_key: str = Field(default="test")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    bcrypt_rounds: int = Field(default=12, ge=10, le=14)

    version: str = Field(default="0.1.0")

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

    # PDF (Jinja2 + WeasyPrint; templates in templates/pdf/ by default)
    pdf_templates_dir: str | None = Field(
        default=None,
        description="Absolute path to folder containing *.html PDF templates; default <project>/templates/pdf",
    )

    # Local media uploads (chunked saves under media_assets_path/{images,videos,files}/)
    media_assets_dir: str | None = Field(
        default=None,
        alias="MEDIA_ASSETS_DIR",
        description="Absolute path to assets root; default <project>/assets",
    )
    assets_url_path_prefix: str = Field(
        default="/api/v1/assets",
        alias="ASSETS_URL_PATH_PREFIX",
        description="URL path prefix for static files (must match FastAPI StaticFiles mount)",
    )
    upload_chunk_size_bytes: int = Field(
        default=1024 * 1024,
        alias="UPLOAD_CHUNK_SIZE_BYTES",
        ge=64 * 1024,
        le=16 * 1024 * 1024,
    )
    max_image_upload_bytes: int = Field(
        default=15 * 1024 * 1024,
        alias="MAX_IMAGE_UPLOAD_BYTES",
        ge=1024,
    )
    max_video_upload_bytes: int = Field(
        default=200 * 1024 * 1024,
        alias="MAX_VIDEO_UPLOAD_BYTES",
        ge=1024,
    )
    max_general_file_upload_bytes: int = Field(
        default=50 * 1024 * 1024,
        alias="MAX_GENERAL_FILE_UPLOAD_BYTES",
        ge=1024,
    )
    accepted_image_types: str = Field(
        default="jpg,jpeg,png,webp",
        alias="ACCEPTED_IMAGE_TYPES",
    )
    accepted_video_types: str = Field(
        default="mp4,mov,avi,webm",
        alias="ACCEPTED_VIDEO_TYPES",
    )
    accepted_file_types: str = Field(
        default="pdf,doc,docx,xls,xlsx,csv,txt",
        alias="ACCEPTED_FILE_TYPES",
    )
    max_batch_upload_files: int = Field(
        default=40,
        alias="MAX_BATCH_UPLOAD_FILES",
        ge=1,
        le=200,
        description="Max files per multi-upload request (auto-detect batch)",
    )

    # Twilio — Programmable SMS (owner OTP custom message) + optional Verify API
    twilio_account_sid: str | None = Field(
        default=None,
        alias="TWILIO_ACCOUNT_SID",
        description="Twilio Account SID (**AC…**). Not a VA… Verify Service SID.",
    )
    twilio_auth_token: str | None = Field(
        default=None,
        alias="TWILIO_AUTH_TOKEN",
        description="Twilio Auth Token (secret—not the AC string).",
    )
    twilio_phone_number: str | None = Field(
        default=None,
        alias="TWILIO_PHONE_NUMBER",
        description="Twilio **sender** for Programmable SMS (E.164 or approved Twilio number) — ``messages.create(..., from_=…)``.",
    )
    twilio_verify_service_sid: str | None = Field(
        default=None,
        alias="TWILIO_VERIFY_SERVICE_SID",
        description="Optional: Verify **Service** SID (**VA…**) for ``start_phone_verification`` / ``check_phone_verification``.",
    )
    twilio_send_sms_in_non_production: bool = Field(
        default=False,
        alias="TWILIO_SEND_SMS_IN_NON_PRODUCTION",
        description="If true, allow Twilio calls from non-production; otherwise skip (local OTP only).",
    )
    twilio_owner_use_verify_for_otp: bool = Field(
        default=False,
        alias="TWILIO_OWNER_USE_VERIFY_FOR_OTP",
        description=(
            "If true, company-owner phone OTP is sent via Twilio Verify (no TWILIO_PHONE_NUMBER / From). "
            "Requires TWILIO_VERIFY_SERVICE_SID (VA…). Use when Programmable SMS would fail (e.g. error 21659)."
        ),
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def media_assets_path(self) -> Path:
        if self.media_assets_dir and str(self.media_assets_dir).strip():
            return Path(self.media_assets_dir).expanduser().resolve()
        return Path(__file__).resolve().parents[2] / "assets"

    def media_extension_allowlist(self, kind: Literal["image", "video", "file"]) -> set[str]:
        raw = {
            "image": self.accepted_image_types,
            "video": self.accepted_video_types,
            "file": self.accepted_file_types,
        }[kind]
        return {x.strip().lower().lstrip(".") for x in raw.split(",") if x.strip()}

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
