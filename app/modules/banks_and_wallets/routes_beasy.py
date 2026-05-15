"""
Beasy — **banks & wallets** catalog (admin).

**Docs:** Each endpoint below sets ``summary`` / ``description`` for Swagger at ``/docs``.

**Auth:** Beasy employee JWT (``Authorization: Bearer``) via ``CurrentEmployeeRequired``.

**Data model:** Rows are banks, wallets, or apps tied to a ``country_id``; the DB column
is ``type`` (``bank`` | ``wallet`` | ``app``); the ORM attribute is ``kind`` (see model).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Query, UploadFile
from pydantic import ValidationError

from app.common.allenums import BankWalletType, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.core.config import get_settings
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.services.media.upload_service import MediaUploadError, save_uploaded_file
from app.modules.banks_and_wallets.schemas import (
    BankAndWalletCreate,
    BankAndWalletRead,
    BankAndWalletUpdate,
)
from app.modules.banks_and_wallets.service import BankAndWalletService

router = APIRouter(prefix="/banks-and-wallets", tags=["Banks & wallets (Beasy)"])


def _svc(db: DbSession) -> BankAndWalletService:
    return BankAndWalletService(db)


@router.get(
    "",
    response_model=ApiResponse[list[BankAndWalletRead]],
    summary="List banks, wallets, and apps",
    description=(
        "Optional filters: ``kind`` (bank | wallet | app), ``is_active`` (true | false). "
        "Omit ``is_active`` to return both active and inactive rows."
    ),
)
def list_banks_and_wallets(
    db: DbSession,
    _: CurrentEmployeeRequired,
    kind: BankWalletType | None = Query(None, description="Filter by catalog type"),
    is_active: bool | None = Query(None, description="Filter by active flag"),
):
    items = _svc(db).list_catalog(
        kind=kind,
        is_active=is_active,
    )
    return json_success(
        [BankAndWalletRead.model_validate(x).model_dump() for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "",
    response_model=ApiResponse[BankAndWalletRead],
    summary="Create catalog entry (multipart)",
    description=(
        "Send ``multipart/form-data`` with fields ``name_ar``, ``name_en``, ``country_id`` (UUID), "
        "``kind`` (``bank`` | ``wallet`` | ``app``), and ``image`` (image file: jpg, jpeg, png, webp). "
        "The image is stored via the shared media upload service; ``country_id`` must exist."
    ),
)
async def create_bank_or_wallet(
    db: DbSession,
    current: CurrentEmployeeRequired,
    name_ar: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    country_id: Annotated[UUID, Form()],
    kind: Annotated[BankWalletType, Form(description="bank | wallet | app")],
    image: Annotated[UploadFile, File(description="Logo or icon image")],
):
    settings = get_settings()
    try:
        upload = await save_uploaded_file(
            image,
            kind="image",
            settings=settings,
            strict_content_type=True,
        )
        data = BankAndWalletCreate(
            name_ar=name_ar,
            name_en=name_en,
            country_id=country_id,
            kind=kind,
            image=upload.file_url,
        )
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    except ValidationError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    try:
        row = _svc(db).create(data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        BankAndWalletRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{row_id}",
    response_model=ApiResponse[BankAndWalletRead],
    summary="Update catalog entry",
    description="Partial update; omit fields you do not want to change. Includes ``is_active``.",
)
def update_bank_or_wallet(
    row_id: UUID,
    data: BankAndWalletUpdate,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    try:
        row = _svc(db).update(str(row_id), data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        BankAndWalletRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete(
    "/{row_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete catalog entry",
    description="Fails if any ``company_financials_accounts`` row still references this id.",
)
def delete_bank_or_wallet(row_id: UUID, db: DbSession, _: CurrentEmployeeRequired):
    try:
        ok = _svc(db).delete(str(row_id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
