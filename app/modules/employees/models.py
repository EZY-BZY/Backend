"""Employee and EmployeePermission models for organization management."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Employee(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Organization employee. Exactly one row must have account_type='owner'.
    Owner is excluded from members listing.
    """

    __tablename__ = "employees"

    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    account_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # soft delete

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
            "account_type IN ('owner', 'admin', 'member')",
            name="ck_employees_account_type",
        ),
        CheckConstraint(
            "account_status IN ('active', 'inactive', 'suspended')",
            name="ck_employees_account_status",
        ),
    )

    permissions = relationship(
        "EmployeePermission",
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EmployeePermission(Base, UUIDPrimaryKeyMixin):
    """Assignment of a permission to an employee. Checked at runtime from DB."""

    __tablename__ = "employee_permissions"

    employee_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "permission_name", name="uq_employee_permissions"),
    )

    employee = relationship("Employee", back_populates="permissions", lazy="selectin")
