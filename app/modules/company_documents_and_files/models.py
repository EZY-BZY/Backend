"""Company documents/files and attached media (documents_media)."""

from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompanyDocumentAndFile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A company document or file record with optional expiry and reminder."""

    __tablename__ = "company_documents_and_files"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    reminder_by_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    media: Mapped[list["DocumentMedia"]] = relationship(
        "DocumentMedia",
        back_populates="company_document",
        cascade="all, delete-orphan",
        order_by="DocumentMedia.created_at",
    )

    __table_args__ = (
        CheckConstraint(
            "document_type IN ("
            "'document', 'commercial_registration', 'tax_card', 'operation_license', "
            "'lease_contract', 'industrial_registration', 'contract', 'other'"
            ")",
            name="ck_company_documents_and_files_document_type",
        ),
        CheckConstraint(
            "reminder_by_days IS NULL OR reminder_by_days >= 0",
            name="ck_company_documents_and_files_reminder_by_days",
        ),
    )


class DocumentMedia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Media attached to a company_documents_and_files row."""

    __tablename__ = "documents_media"

    company_document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_documents_and_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    media_type: Mapped[str] = mapped_column(String(16), nullable=False)
    media_link: Mapped[str] = mapped_column(String(2048), nullable=False)

    company_document: Mapped["CompanyDocumentAndFile"] = relationship(
        "CompanyDocumentAndFile",
        back_populates="media",
    )

    __table_args__ = (
        CheckConstraint(
            "media_type IN ('images', 'videos', 'files')",
            name="ck_documents_media_media_type",
        ),
    )
