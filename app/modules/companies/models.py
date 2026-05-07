"""Company ORM model (owned by a company owner)."""

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A business profile created by a company owner."""

    __tablename__ = "companies"

    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies_owners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    company_name_ar: Mapped[str] = mapped_column(String(256), nullable=False)
    company_name_en: Mapped[str | None] = mapped_column(String(256), nullable=True)
    company_description_ar: Mapped[str] = mapped_column(Text, nullable=False)
    company_description_en: Mapped[str | None] = mapped_column(Text, nullable=True)

    show_branches: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    show_products: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    show_social_media: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    show_contact_info: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="active",
        index=True,
    )

    image: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    service: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(38, 8),
        nullable=False,
        doc="Signed balance; wide precision for large magnitudes.",
    )

    tax_number: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_companies_status",
        ),
        CheckConstraint(
            "service IN ('services', 'products', 'products_and_services')",
            name="ck_companies_service",
        ),
    )
