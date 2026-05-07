"""Pydantic schemas for company_documents_and_files and documents_media."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.allenums import CompanyDocumentType, DocumentMediaKind


class DocumentMediaCreate(BaseModel):
    media_type: DocumentMediaKind
    media_link: str = Field(..., min_length=1, max_length=2048)

    @field_validator("media_link", mode="before")
    @classmethod
    def _strip_link(cls, v: str) -> str:
        return str(v).strip()


class DocumentMediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_document_id: UUID
    media_type: DocumentMediaKind
    media_link: str
    created_at: datetime
    updated_at: datetime


class CompanyDocumentAndFileCreate(BaseModel):
    document_type: CompanyDocumentType
    expiry_date: date
    reminder_by_days: int | None = Field(
        None,
        ge=0,
        description="Notify this many days before expiry; omit or null for no reminder.",
    )


class CompanyDocumentAndFileUpdate(BaseModel):
    document_type: CompanyDocumentType | None = None
    expiry_date: date | None = None
    reminder_by_days: int | None = Field(None, ge=0)


class CompanyDocumentAndFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    document_type: CompanyDocumentType
    expiry_date: date
    reminder_by_days: int | None
    media: list[DocumentMediaRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CompanyDocumentAndFileBeasyRead(CompanyDocumentAndFileRead):
    model_config = ConfigDict(
        from_attributes=True,
        title="CompanyDocumentAndFile",
    )
