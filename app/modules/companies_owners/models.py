"""Company owners ORM model."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompanyOwner(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Company owner account created by client registration."""

    __tablename__ = "companies_owners"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)

    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    last_accepted_terms_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    otp_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified_phone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    forgot_password_otp_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    forgot_password_otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    forgot_password_otp_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    forgot_password_verify_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    forgot_password_resend_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    forgot_password_last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    join_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    account_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="pending_verification",
        index=True,
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

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('active', 'pending_verification', 'suspended', 'blocked', 'deleted')",
            name="ck_companies_owners_account_status",
        ),
    )

