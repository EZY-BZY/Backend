"""Industry ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Industry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Business industry vertical (multilingual names + media path/URL)."""

    __tablename__ = "industries"

    name_en: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(256), nullable=False)
    image: Mapped[str] = mapped_column(String(2048), nullable=False)

    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    company_industry_links: Mapped[list["CompanyIndustry"]] = relationship(
        "CompanyIndustry",
        back_populates="industry",
    )
