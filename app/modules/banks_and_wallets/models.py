"""Bank, wallet, or payment app catalog entry (Beasy-managed)."""

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BankAndWallet(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Master list of banks, wallets, and apps (per country)."""

    __tablename__ = "banks_and_wallets"

    name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    name_en: Mapped[str] = mapped_column(String(256), nullable=False)
    image: Mapped[str] = mapped_column(String(2048), nullable=False)

    country_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    kind: Mapped[str] = mapped_column(
        "type",
        String(16),
        nullable=False,
        index=True,
    )

    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('bank', 'wallet', 'app')",
            name="ck_banks_and_wallets_type",
        ),
    )
