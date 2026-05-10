"""Company employees, phone numbers, and app permission assignments."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompanyEmployee(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Staff member belonging to a company (client app)."""

    __tablename__ = "company_employees"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    email: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    salary: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    bonus_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0"
    )
    salary_system: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    created_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    phones: Mapped[list["CompanyEmployeePhone"]] = relationship(
        "CompanyEmployeePhone",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="CompanyEmployeePhone.created_at",
    )
    app_permissions: Mapped[list["EmployeeAppPermission"]] = relationship(
        "EmployeeAppPermission",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'employee', 'inventory_manager', 'finance')",
            name="ck_company_employees_role",
        ),
        CheckConstraint(
            "salary_system IS NULL OR salary_system IN ('monthly', 'weekly', 'yearly', 'daily')",
            name="ck_company_employees_salary_system",
        ),
        CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_company_employees_created_by_type",
        ),
        CheckConstraint(
            "updated_by_type IN ('company_owner', 'employee')",
            name="ck_company_employees_updated_by_type",
        ),
        CheckConstraint("salary IS NULL OR salary >= 0", name="ck_company_employees_salary_nonneg"),
        CheckConstraint("bonus_amount >= 0", name="ck_company_employees_bonus_nonneg"),
    )


class CompanyEmployeePhone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Phone number for a company employee (globally unique)."""

    __tablename__ = "company_employee_phones"

    employee_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    created_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    employee: Mapped["CompanyEmployee"] = relationship("CompanyEmployee", back_populates="phones")

    __table_args__ = (
        CheckConstraint(
            "created_by_type IN ('company_owner', 'employee')",
            name="ck_company_employee_phones_created_by_type",
        ),
        CheckConstraint(
            "updated_by_type IN ('company_owner', 'employee')",
            name="ck_company_employee_phones_updated_by_type",
        ),
        Index(
            "uq_company_employee_phones_one_primary_active",
            "employee_id",
            unique=True,
            postgresql_where=text("is_primary IS TRUE AND is_active IS TRUE"),
        ),
    )


class EmployeeAppPermission(Base, UUIDPrimaryKeyMixin):
    """Assignment of an app permission to a company employee."""

    __tablename__ = "employees_app_permissions"

    employee_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("company_employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_permission_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("app_permissions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    assigned_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    updated_by_type: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    employee: Mapped["CompanyEmployee"] = relationship("CompanyEmployee", back_populates="app_permissions")
    app_permission: Mapped["AppPermission"] = relationship("AppPermission", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "app_permission_id",
            name="uq_employees_app_permissions_employee_perm",
        ),
        CheckConstraint(
            "assigned_by_type IN ('company_owner', 'employee')",
            name="ck_employees_app_permissions_assigned_by_type",
        ),
        CheckConstraint(
            "updated_by_type IN ('company_owner', 'employee')",
            name="ck_employees_app_permissions_updated_by_type",
        ),
    )
