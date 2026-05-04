"""Terms and terms_history ORM models."""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Term(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Legal/application term content; multiple rows per `type`, ordered by `order`."""

    __tablename__ = "terms"

    sort_order: Mapped[int] = mapped_column("order", Integer, nullable=False)
    name_en: Mapped[str] = mapped_column(String(512), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(512), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(512), nullable=False)
    description_en: Mapped[str] = mapped_column(Text, nullable=False)
    description_ar: Mapped[str] = mapped_column(Text, nullable=False)
    description_fr: Mapped[str] = mapped_column(Text, nullable=False)
    term_type: Mapped[str] = mapped_column("type", String(32), nullable=False, index=True)

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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('privacy_policy', 'terms_of_use', 'refund_terms', 'delivery_terms')",
            name="ck_terms_type",
        ),
    )


class TermHistory(Base, UUIDPrimaryKeyMixin):
    """
    One version row per CUD action: full ordered list of terms for that type
    after the change, stored in `terms_snapshot` JSON (see service for shape).
    """

    __tablename__ = "terms_history"

    term_type: Mapped[str] = mapped_column(
        "term_type", String(32), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    performed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    changed_term_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("terms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    terms_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "action IN ('created', 'updated', 'deleted')",
            name="ck_terms_history_action",
        ),
        CheckConstraint(
            "term_type IN ('privacy_policy', 'terms_of_use', 'refund_terms', 'delivery_terms')",
            name="ck_terms_history_term_type",
        ),
    )
