"""Data access for app_permissions and history."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.app_permissions.models import AppPermission, AppPermissionHistory


class AppPermissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, permission_id: str) -> AppPermission | None:
        return self.db.get(AppPermission, permission_id)

    def get_by_id_active(self, permission_id: str) -> AppPermission | None:
        row = self.db.get(AppPermission, permission_id)
        if row is None or not row.is_active:
            return None
        return row

    def get_by_permission_key(self, permission_key: str) -> AppPermission | None:
        stmt = select(AppPermission).where(AppPermission.permission_key == permission_key)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[AppPermission]:
        stmt = select(AppPermission).order_by(AppPermission.permission_key.asc())
        return list(self.db.execute(stmt).scalars().all())

    def list_active(self) -> list[AppPermission]:
        stmt = (
            select(AppPermission)
            .where(AppPermission.is_active.is_(True))
            .order_by(AppPermission.permission_key.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_history_for_permission(self, permission_id: str) -> list[AppPermissionHistory]:
        stmt = (
            select(AppPermissionHistory)
            .where(AppPermissionHistory.app_permission_id == permission_id)
            .order_by(AppPermissionHistory.performed_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, row: AppPermission) -> AppPermission:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
