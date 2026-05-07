"""Company fixed assets and attached media rows."""

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FixedAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A tangible company asset (vehicles, property, equipment, etc.)."""

    __tablename__ = "fixed_assets"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asset_name: Mapped[str] = mapped_column(String(512), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    location_description: Mapped[str] = mapped_column(Text, nullable=False)

    media: Mapped[list["AssetMedia"]] = relationship(
        "AssetMedia",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="AssetMedia.created_at",
    )

    __table_args__ = (
        CheckConstraint(
            "asset_type IN ("
            "'cars_and_trucks', 'building_and_real_estate', 'machines', "
            "'computers', 'office_furniture', 'other'"
            ")",
            name="ck_fixed_assets_asset_type",
        ),
    )


class AssetMedia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Media attachment for a fixed asset (image, document URL, etc.)."""

    __tablename__ = "assets_media"

    asset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fixed_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    media_link: Mapped[str] = mapped_column(String(2048), nullable=False)

    asset: Mapped["FixedAsset"] = relationship("FixedAsset", back_populates="media")
