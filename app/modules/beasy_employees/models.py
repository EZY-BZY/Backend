"""B-easy employee ORM model."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BEasyEmployee(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    B-easy employee. Exactly one row must have account_type='Super User'.
    Super User is excluded from members listing.
    """

    # SQL name mirrors the product ("Beasy employees"); use underscores, not hyphens.
    __tablename__ = "beasy_employees"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    account_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # soft delete

    created_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "account_type IN ('super_user', 'admin', 'member')",
            name="ck_employees_account_type",
        ),
        CheckConstraint(
            "account_status IN ('active', 'inactive', 'suspended')",
            name="ck_employees_account_status",
        ),
    )
