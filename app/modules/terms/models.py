"""Terms and conditions model with multilingual content."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Term(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Terms and conditions content. Supports Arabic, English, French."""

    __tablename__ = "terms"

    term_title_ar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    term_title_en: Mapped[str | None] = mapped_column(String(512), nullable=True)
    term_title_fr: Mapped[str | None] = mapped_column(String(512), nullable=True)
    term_desc_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    term_desc_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    term_desc_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    term_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    term_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="valid", index=True)

    created_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "term_type IN ('privacy_policy', 'terms_of_use', 'cookies_terms')",
            name="ck_terms_term_type",
        ),
        CheckConstraint(
            "status IN ('valid', 'invalid')",
            name="ck_terms_status",
        ),
    )
