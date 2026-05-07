"""Company contact info entries (phone, social handles, etc.)."""

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompanyContactInfo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One labeled contact method for a company."""

    __tablename__ = "company_contact_infos"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    value: Mapped[str] = mapped_column(String(2048), nullable=False)
    contact_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    __table_args__ = (
        CheckConstraint(
            "contact_type IN ("
            "'number', 'facebook', 'instagram', 'tiktok', 'youtube', "
            "'threads', 'whatsapp', 'twitter_x'"
            ")",
            name="ck_company_contact_infos_contact_type",
        ),
    )
