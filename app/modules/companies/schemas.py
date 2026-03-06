"""Company Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    """Base company fields."""

    name: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    is_active: bool = True


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""

    pass


class CompanyUpdate(BaseModel):
    """Schema for partial company update."""

    name: str | None = Field(None, min_length=1, max_length=256)
    slug: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    is_active: bool | None = None


class CompanyRead(CompanyBase):
    """Company response schema."""

    id: UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
