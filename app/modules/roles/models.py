"""Role and Permission models. Scoped per company (tenant)."""

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.base import TimestampMixin, UUIDPrimaryKeyMixin


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Role within a company. Each company has its own roles."""

    __tablename__ = "roles"

    company_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_roles_company_name"),)

    company = relationship("Company", back_populates="roles", lazy="selectin")
    role_permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles = relationship("UserRole", back_populates="role", lazy="selectin")


class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Permission (global). Keyed by code; roles get permissions via RolePermission."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    role_permissions = relationship(
        "RolePermission", back_populates="permission", lazy="selectin"
    )


class RolePermission(Base, UUIDPrimaryKeyMixin):
    """Association: Role has many Permissions."""

    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    role = relationship("Role", back_populates="role_permissions", lazy="selectin")
    permission = relationship("Permission", back_populates="role_permissions", lazy="selectin")
