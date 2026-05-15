"""
Clients — read-only **app permissions** catalog (active rows only).

**Base path:** ``/clients/app-permissions``

**Auth:** None (same idea as the banks & wallets client catalog). Only ``is_active=true`` rows.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.app_permissions.schemas import AppPermissionClientRead
from app.modules.app_permissions.service import AppPermissionService

router = APIRouter(prefix="/app-permissions", tags=["App permissions (clients)"])


def _svc(db: DbSession) -> AppPermissionService:
    return AppPermissionService(db)


@router.get(
    "",
    response_model=ApiResponse[list[AppPermissionClientRead]],
    summary="List active app permissions",
)
def list_active_app_permissions(db: DbSession):
    items = _svc(db).list_active()
    return json_success(
        [AppPermissionClientRead.model_validate(x).model_dump(mode="json") for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


# @router.get(
#     "/{permission_id}",
#     response_model=ApiResponse[AppPermissionClientRead],
#     summary="Get one active app permission by id",
# )
# def get_active_app_permission(permission_id: UUID, db: DbSession):
#     row = _svc(db).get_by_id_active(str(permission_id))
#     if row is None:
#         return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
#     return json_success(
#         AppPermissionClientRead.model_validate(row).model_dump(mode="json"),
#         message=ResponseEnum.SUCCESS.value,
#     )
