"""
Clients — **fixed assets** for one company (owner CRUD + media).

**Base path:** ``/clients/companies/{company_id}/fixed-assets``.

**Auth:** Owner JWT; ``company_id`` must belong to the authenticated owner.

**Responses:** Each asset includes ``media`` (from ``assets_media``). JSON uses the key
``type`` for the asset category (see ``FixedAssetType`` enum values).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.fixed_assets.schemas import (
    FixedAssetCreate,
    FixedAssetMediaCreate,
    FixedAssetMediaRead,
    FixedAssetRead,
    FixedAssetUpdate,
)
from app.modules.fixed_assets.service import FixedAssetService

router = APIRouter(
    prefix="/companies/{company_id}/fixed-assets",
    tags=["Fixed assets (clients)"],
)


def _svc(db: DbSession) -> FixedAssetService:
    return FixedAssetService(db)


def _dump_asset(row) -> dict:
    return FixedAssetRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[FixedAssetRead]],
    summary="List fixed assets for a company",
    description="404 if the company is missing or not owned by you. Each item includes nested ``media``.",
)
def list_fixed_assets(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    items = _svc(db).list_for_owner(str(company_id), current["user_id"])
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [_dump_asset(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "",
    response_model=ApiResponse[FixedAssetRead],
    summary="Create a fixed asset",
)
def create_fixed_asset(
    company_id: UUID,
    data: FixedAssetCreate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).create(str(company_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump_asset(row), message=ResponseEnum.SUCCESS.value)


@router.get(
    "/{asset_id}",
    response_model=ApiResponse[FixedAssetRead],
    summary="Get one fixed asset",
    description="Includes all ``assets_media`` rows for this asset.",
)
def get_fixed_asset(
    company_id: UUID,
    asset_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    row = _svc(db).get_for_owner(str(company_id), str(asset_id), current["user_id"])
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_asset(row), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{asset_id}",
    response_model=ApiResponse[FixedAssetRead],
    summary="Update a fixed asset",
)
def update_fixed_asset(
    company_id: UUID,
    asset_id: UUID,
    data: FixedAssetUpdate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).update(str(company_id), str(asset_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_asset(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{asset_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete a fixed asset",
    description="Cascade-deletes related ``assets_media`` rows.",
)
def delete_fixed_asset(
    company_id: UUID,
    asset_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    ok = _svc(db).delete(str(company_id), str(asset_id), current["user_id"])
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/{asset_id}/media",
    response_model=ApiResponse[FixedAssetMediaRead],
    summary="Attach media to a fixed asset",
)
def add_fixed_asset_media(
    company_id: UUID,
    asset_id: UUID,
    data: FixedAssetMediaCreate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        m = _svc(db).add_media(str(company_id), str(asset_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if m is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        FixedAssetMediaRead.model_validate(m).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete(
    "/{asset_id}/media/{media_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Remove one media row from a fixed asset",
)
def delete_fixed_asset_media(
    company_id: UUID,
    asset_id: UUID,
    media_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    ok = _svc(db).delete_media(
        str(company_id), str(asset_id), str(media_id), current["user_id"]
    )
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
