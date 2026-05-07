"""
Clients — **fixed assets** for one company (owner CRUD + media).

**Base path:** ``/clients/companies/{company_id}/fixed-assets``.

**Auth:** Owner JWT; ``company_id`` must belong to the authenticated owner.

**Create & add-media:** ``multipart/form-data`` — text fields plus optional file parts
(repeat field name ``files`` for multiple uploads). Stored ``media_type`` is
``image`` / ``video`` / ``file`` (from auto-detection).

**Other routes:** JSON where applicable (e.g. PATCH). Responses use ``type`` for the asset category.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import ValidationError

from app.common.allenums import FixedAssetType, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.core.config import get_settings
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.fixed_assets.schemas import FixedAssetCreate, FixedAssetMediaRead, FixedAssetRead, FixedAssetUpdate
from app.modules.fixed_assets.service import FixedAssetService
from app.services.media.owner_upload_helpers import fixed_asset_media_type_from_upload
from app.services.media.upload_service import MediaUploadError, save_uploaded_file_auto

router = APIRouter(
    prefix="/companies/{company_id}/fixed-assets",
    tags=["Fixed assets (clients)"],
)


def _svc(db: DbSession) -> FixedAssetService:
    return FixedAssetService(db)


def _dump_asset(row) -> dict:
    return FixedAssetRead.model_validate(row).model_dump(by_alias=True, mode="json")


async def _upload_pairs_for_fixed_assets(files: list[UploadFile]) -> list[tuple[str, str]]:
    settings = get_settings()
    pairs: list[tuple[str, str]] = []
    for upload in files:
        result = await save_uploaded_file_auto(upload, settings=settings, strict_content_type=False)
        pairs.append((fixed_asset_media_type_from_upload(result.file_type), result.file_url))
    return pairs


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
    summary="Create a fixed asset (multipart)",
    description=(
        "Send ``multipart/form-data``: fields ``asset_name``, ``type``, ``details``, "
        "``location_description``; optional repeated ``files`` for uploads."
    ),
)
async def create_fixed_asset(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
    asset_name: Annotated[str, Form()],
    type: Annotated[  # noqa: A001
        FixedAssetType,
        Form(description="Asset category (same values as JSON API)."),
    ],
    details: Annotated[str, Form()],
    location_description: Annotated[str, Form()],
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    settings = get_settings()
    uploads = [f for f in (files or []) if f.filename]
    if len(uploads) > settings.max_batch_upload_files:
        return json_error(
            ResponseEnum.FAIL.value,
            http_status=400,
            details=f"Too many files. Maximum is {settings.max_batch_upload_files}.",
        )
    try:
        data = FixedAssetCreate(
            asset_name=asset_name,
            asset_type=type,
            details=details,
            location_description=location_description,
        )
    except ValidationError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    try:
        if uploads:
            media_pairs = await _upload_pairs_for_fixed_assets(uploads)
            row = _svc(db).create_with_media_urls(str(company_id), current["user_id"], data, media_pairs)
        else:
            row = _svc(db).create(str(company_id), current["user_id"], data)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
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
    summary="Attach media (multipart file)",
    description="``multipart/form-data`` with a single ``file`` part; type is detected automatically.",
)
async def add_fixed_asset_media(
    company_id: UUID,
    asset_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
    file: Annotated[UploadFile, File(..., description="Image, video, or document")],
):
    settings = get_settings()
    try:
        result = await save_uploaded_file_auto(file, settings=settings, strict_content_type=False)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    media_type = fixed_asset_media_type_from_upload(result.file_type)
    try:
        m = _svc(db).add_media_from_url(
            str(company_id),
            str(asset_id),
            current["user_id"],
            media_type=media_type,
            media_link=result.file_url,
        )
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
