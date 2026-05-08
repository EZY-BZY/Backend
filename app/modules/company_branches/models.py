"""Company branches, contacts, and working hours."""

from __future__ import annotations

from datetime import time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompanyBranch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A company location (factory, warehouse, showroom, office)."""

    __tablename__ = "company_branches"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    branch_name: Mapped[str] = mapped_column(String(512), nullable=False)
    branch_location_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    branch_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)
    is_visible_to_clients: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
    )

    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    contacts: Mapped[list["CompanyBranchContact"]] = relationship(
        "CompanyBranchContact",
        back_populates="branch",
        cascade="all, delete-orphan",
        order_by="CompanyBranchContact.created_at",
    )
    working_hours: Mapped[list["CompanyBranchWorkingHours"]] = relationship(
        "CompanyBranchWorkingHours",
        back_populates="branch",
        cascade="all, delete-orphan",
        order_by="CompanyBranchWorkingHours.day_of_week",
    )

    __table_args__ = (
        CheckConstraint(
            "branch_type IN ('factory', 'warehouse', 'showroom', 'office')",
            name="ck_company_branches_branch_type",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_company_branches_lat_lon_pair",
        ),
    )


class CompanyBranchContact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Phone / contact person for a branch."""

    __tablename__ = "company_branch_contacts"

    branch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact_name: Mapped[str] = mapped_column(String(256), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(64), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    branch: Mapped["CompanyBranch"] = relationship("CompanyBranch", back_populates="contacts")

    __table_args__ = (
        Index(
            "uq_company_branch_contacts_one_primary_active",
            "branch_id",
            unique=True,
            postgresql_where=text("is_primary IS TRUE AND is_active IS TRUE"),
        ),
    )


class CompanyBranchWorkingHours(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One row per branch per weekday."""

    __tablename__ = "company_branch_working_hours"

    branch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    day_of_week: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    is_day_off: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    opening_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    closing_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    branch: Mapped["CompanyBranch"] = relationship("CompanyBranch", back_populates="working_hours")

    __table_args__ = (
        CheckConstraint(
            "day_of_week IN ("
            "'saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday'"
            ")",
            name="ck_company_branch_working_hours_day",
        ),
        CheckConstraint(
            "(is_day_off = true AND opening_time IS NULL AND closing_time IS NULL) "
            "OR (is_day_off = false AND opening_time IS NOT NULL AND closing_time IS NOT NULL "
            "AND closing_time > opening_time)",
            name="ck_company_branch_working_hours_times",
        ),
        UniqueConstraint("branch_id", "day_of_week", name="uq_company_branch_working_hours_branch_day"),
    )
