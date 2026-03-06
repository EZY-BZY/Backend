"""Pydantic schemas for terms and conditions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.terms.enums import TermStatus, TermType


class TermBase(BaseModel):
    """Shared fields for term."""

    term_title_ar: str | None = Field(None, max_length=512)
    term_title_en: str | None = Field(None, max_length=512)
    term_title_fr: str | None = Field(None, max_length=512)
    term_desc_ar: str | None = None
    term_desc_en: str | None = None
    term_desc_fr: str | None = None
    term_order: int = Field(0, ge=0)
    term_type: TermType
    status: TermStatus = TermStatus.VALID


class TermCreate(TermBase):
    """Create term."""

    pass


class TermUpdate(BaseModel):
    """Partial update for term."""

    term_title_ar: str | None = Field(None, max_length=512)
    term_title_en: str | None = Field(None, max_length=512)
    term_title_fr: str | None = Field(None, max_length=512)
    term_desc_ar: str | None = None
    term_desc_en: str | None = None
    term_desc_fr: str | None = None
    term_order: int | None = Field(None, ge=0)
    term_type: TermType | None = None
    status: TermStatus | None = None


class TermRead(TermBase):
    """Term response."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID | None
    updated_by_id: UUID | None

    model_config = {"from_attributes": True}


class TermReadByLanguage(BaseModel):
    """Term content for a given language (e.g. title_en, desc_en)."""

    id: UUID
    title: str | None
    description: str | None
    term_order: int
    term_type: str
    status: str
    created_at: datetime
    updated_at: datetime
