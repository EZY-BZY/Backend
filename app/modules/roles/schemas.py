"""Role and Permission Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(..., max_length=64)
    description: str | None = None


class RoleCreate(RoleBase):
    company_id: UUID  # Set by route from context


class RoleRead(RoleBase):
    id: UUID
    company_id: UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PermissionRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
