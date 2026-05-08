"""Business logic for app_permissions."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.app_permissions.enums import AppPermissionHistoryAction
from app.modules.app_permissions.models import AppPermission, AppPermissionHistory
from app.modules.app_permissions.repository import AppPermissionRepository
from app.modules.app_permissions.schemas import AppPermissionCreate, AppPermissionUpdate


def _row_snapshot(row: AppPermission) -> dict:
    return {
        "permission_tag": row.permission_tag,
        "permission_label": row.permission_label,
        "permission_key": row.permission_key,
        "description": row.description,
        "is_active": row.is_active,
    }


class AppPermissionService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = AppPermissionRepository(db)

    def list_all(self) -> list[AppPermission]:
        return self._repo.list_all()

    def list_active(self) -> list[AppPermission]:
        return self._repo.list_active()

    def get_by_id(self, permission_id: str) -> AppPermission | None:
        return self._repo.get_by_id(permission_id)

    def get_by_id_active(self, permission_id: str) -> AppPermission | None:
        return self._repo.get_by_id_active(permission_id)

    def list_history(self, permission_id: str) -> list[AppPermissionHistory]:
        return self._repo.list_history_for_permission(permission_id)

    def create(self, data: AppPermissionCreate, actor_id: str) -> AppPermission:
        row = AppPermission(
            permission_tag=data.permission_tag,
            permission_label=data.permission_label,
            permission_key=data.permission_key,
            description=data.description,
            is_active=data.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create permission (duplicate permission_key?).") from e

    def update(self, permission_id: str, data: AppPermissionUpdate, actor_id: str) -> AppPermission | None:
        row = self._repo.get_by_id(permission_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        hist = AppPermissionHistory(
            app_permission_id=row.id,
            permission_key=row.permission_key,
            action=AppPermissionHistoryAction.UPDATED.value,
            performed_by=actor_id,
            snapshot=_row_snapshot(row),
        )
        self._db.add(hist)
        if "permission_key" in payload and payload["permission_key"] is not None:
            row.permission_key = payload["permission_key"]
            del payload["permission_key"]
        for k, v in payload.items():
            setattr(row, k, v)
        row.updated_by = actor_id
        try:
            self._db.commit()
            self._db.refresh(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update permission (duplicate permission_key?).") from e
        return row

    def delete(self, permission_id: str, actor_id: str) -> bool:
        row = self._repo.get_by_id(permission_id)
        if row is None:
            return False
        hist = AppPermissionHistory(
            app_permission_id=row.id,
            permission_key=row.permission_key,
            action=AppPermissionHistoryAction.DELETED.value,
            performed_by=actor_id,
            snapshot=_row_snapshot(row),
        )
        self._db.add(hist)
        self._db.delete(row)
        try:
            self._db.commit()
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not delete permission.") from e
        return True
