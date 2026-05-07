"""Company-linked bank / wallet / app account numbers."""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompanyFinancialsAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A company's financial account at a catalogued bank, wallet, or app."""

    __tablename__ = "company_financials_accounts"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    banks_and_wallets_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("banks_and_wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    account_number: Mapped[str] = mapped_column(String(256), nullable=False)
    account_name: Mapped[str] = mapped_column(String(256), nullable=False)

    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies_owners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        doc="When false, account can be hidden from public/storefront UIs while kept in DB.",
    )
