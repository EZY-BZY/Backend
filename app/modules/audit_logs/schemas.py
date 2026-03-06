"""Audit log Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    action: str = Field(..., max_length=128)
    target_type: str = Field(..., max_length=64)
    target_id: str | None = None
    metadata: dict | None = None
    note: str | None = None


class AuditLogRead(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    company_id: UUID | None
    action: str
    target_type: str
    target_id: str | None
    metadata: dict | None
    note: str | None
    created_at: str

    model_config = {"from_attributes": True}
