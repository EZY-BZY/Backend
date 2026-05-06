"""Country ORM model."""

from datetime import date

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Country(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """System country metadata with multilingual names and phone validation."""

    __tablename__ = "countries"

    phone_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)

    name_en: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(256), nullable=False)

    phone_regex: Mapped[str] = mapped_column(String(512), nullable=False)

    currency_shortcut_en: Mapped[str] = mapped_column(String(16), nullable=False)
    currency_shortcut_ar: Mapped[str] = mapped_column(String(16), nullable=False)
    currency_shortcut_fr: Mapped[str] = mapped_column(String(16), nullable=False)
    currency_name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    currency_name_ar: Mapped[str] = mapped_column(String(128), nullable=False)
    currency_name_fr: Mapped[str] = mapped_column(String(128), nullable=False)

    flag_emoji: Mapped[str] = mapped_column(
        "icon",
        String(16),
        nullable=False,
        doc="Country flag emoji (e.g. 🇪🇬). Stored as text.",
    )

    created_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        doc="Creation date (date-only, UTC).",
    )

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

