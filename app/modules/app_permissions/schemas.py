"""Pydantic schemas for app_permissions."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_PERMISSION_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


class AppPermissionCreate(BaseModel):
    permission_tag: str = Field(..., min_length=1, max_length=128)
    permission_label: str = Field(..., min_length=1, max_length=64)
    permission_key: str = Field(..., min_length=1, max_length=256)
    description: str | None = Field(None, max_length=4096)
    is_active: bool = True

    @field_validator("permission_tag", "permission_label", mode="before")
    @classmethod
    def _strip_tag_label(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("permission_key", mode="before")
    @classmethod
    def _normalize_key(cls, v: str) -> str:
        s = str(v).strip().lower()
        if not _PERMISSION_KEY_RE.match(s):
            raise ValueError(
                "permission_key must look like dotted segments (e.g. users.view, company_docs.delete)."
            )
        return s

    @field_validator("description", mode="before")
    @classmethod
    def _strip_desc(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class AppPermissionUpdate(BaseModel):
    permission_tag: str | None = Field(None, min_length=1, max_length=128)
    permission_label: str | None = Field(None, min_length=1, max_length=64)
    permission_key: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = Field(None, max_length=4096)
    is_active: bool | None = None

    @field_validator("permission_tag", "permission_label", mode="before")
    @classmethod
    def _strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return str(v).strip()

    @field_validator("permission_key", mode="before")
    @classmethod
    def _normalize_key_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip().lower()
        if not _PERMISSION_KEY_RE.match(s):
            raise ValueError(
                "permission_key must look like dotted segments (e.g. users.view, company_docs.delete)."
            )
        return s

    @field_validator("description", mode="before")
    @classmethod
    def _strip_desc_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class AppPermissionRead(BaseModel):
    """Full row for Beasy."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    permission_tag: str
    permission_label: str
    permission_key: str
    description: str | None
    is_active: bool
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class AppPermissionClientRead(BaseModel):
    """Client API: active catalog only (no audit ids)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    permission_tag: str
    permission_label: str
    permission_key: str
    description: str | None


class AppPermissionHistoryRead(BaseModel):
    """One history event (state before update, or before delete)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    app_permission_id: UUID | None
    permission_key: str
    action: str
    performed_by: UUID | None
    performed_at: datetime
    snapshot: dict
