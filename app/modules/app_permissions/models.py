"""Application permission catalog and change history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AppPermission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A logical permission (checked via ``permission_key``, not URLs)."""

    __tablename__ = "app_permissions"

    permission_tag: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    permission_label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    permission_key: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
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


class AppPermissionHistory(Base, UUIDPrimaryKeyMixin):
    """Prior state before an update, or final state before a delete (no FK to live row)."""

    __tablename__ = "app_permissions_history"

    app_permission_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        index=True,
    )
    permission_key: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    performed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("beasy_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "action IN ('updated', 'deleted')",
            name="ck_app_permissions_history_action",
        ),
    )
