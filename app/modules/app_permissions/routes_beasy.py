"""Beasy: full CRUD for app_permissions + history read."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.app_permissions.schemas import (
    AppPermissionCreate,
    AppPermissionHistoryRead,
    AppPermissionRead,
    AppPermissionUpdate,
)
from app.modules.app_permissions.service import AppPermissionService
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired

router = APIRouter(prefix="/app-permissions", tags=["App permissions (Beasy)"])


def _svc(db: DbSession) -> AppPermissionService:
    return AppPermissionService(db)


@router.post("", response_model=ApiResponse[AppPermissionRead], summary="Create app permission")
def create_app_permission(
    data: AppPermissionCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    try:
        row = _svc(db).create(data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        AppPermissionRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "",
    response_model=ApiResponse[list[AppPermissionRead]],
    summary="List all app permissions",
    description="Includes inactive rows. Clients use ``/clients/app-permissions`` for active only.",
)
def list_app_permissions(db: DbSession, _: CurrentEmployeeRequired):
    items = _svc(db).list_all()
    return json_success(
        [AppPermissionRead.model_validate(x).model_dump(mode="json") for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{permission_id}/history",
    response_model=ApiResponse[list[AppPermissionHistoryRead]],
    summary="List change history for one permission id",
    description="Includes events after the row was deleted (matched by stored id / key).",
)
def list_app_permission_history(
    permission_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    rows = _svc(db).list_history(str(permission_id))
    return json_success(
        [AppPermissionHistoryRead.model_validate(x).model_dump(mode="json") for x in rows],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{permission_id}",
    response_model=ApiResponse[AppPermissionRead],
    summary="Get app permission by id",
)
def get_app_permission(
    permission_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    row = _svc(db).get_by_id(str(permission_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        AppPermissionRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{permission_id}",
    response_model=ApiResponse[AppPermissionRead],
    summary="Update app permission",
    description="Appends a history row with the **previous** field values.",
)
def update_app_permission(
    permission_id: UUID,
    data: AppPermissionUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    try:
        row = _svc(db).update(str(permission_id), data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        AppPermissionRead.model_validate(row).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete(
    "/{permission_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete app permission",
    description="Hard delete after recording a history snapshot of the row.",
)
def delete_app_permission(
    permission_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    try:
        ok = _svc(db).delete(str(permission_id), actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
