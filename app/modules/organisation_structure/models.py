"""Organisation structure (department) records per company."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrganisationStructure(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A department / org unit within a company."""

    __tablename__ = "organisation_structures"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name_en: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department_establish_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    total_salaries: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0"
    )
    total_employees: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    employees: Mapped[list["CompanyEmployee"]] = relationship(
        "CompanyEmployee",
        back_populates="organisation_structure",
    )
