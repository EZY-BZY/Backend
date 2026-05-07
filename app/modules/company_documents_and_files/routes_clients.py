"""
Clients — **company documents & files** (owner CRUD + documents_media).

**Base path:** ``/clients/companies/{company_id}/documents-and-files``.

**Auth:** Owner JWT. Each document row includes nested ``media`` (``documents_media``).

**Create & add-media:** ``multipart/form-data`` with optional repeated ``files``.
Detected uploads map to ``media_type`` ``images`` / ``videos`` / ``files``.

**PATCH** remains JSON. ``expiry_date`` on create is an ISO date string (e.g. ``2026-12-31``).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import ValidationError

from app.common.allenums import CompanyDocumentType, DocumentMediaKind, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.core.config import get_settings
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.company_documents_and_files.schemas import (
    CompanyDocumentAndFileCreate,
    CompanyDocumentAndFileRead,
    CompanyDocumentAndFileUpdate,
    DocumentMediaCreate,
    DocumentMediaRead,
)
from app.modules.company_documents_and_files.service import CompanyDocumentAndFileService
from app.services.media.owner_upload_helpers import document_media_kind_from_upload
from app.services.media.upload_service import MediaUploadError, save_uploaded_file_auto

router = APIRouter(
    prefix="/companies/{company_id}/documents-and-files",
    tags=["Company documents & files (clients)"],
)


def _svc(db: DbSession) -> CompanyDocumentAndFileService:
    return CompanyDocumentAndFileService(db)


def _dump_doc(row) -> dict:
    return CompanyDocumentAndFileRead.model_validate(row).model_dump(mode="json")


def _parse_reminder(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    return int(s)


async def _upload_pairs_for_documents(
    files: list[UploadFile],
) -> list[tuple[DocumentMediaKind, str]]:
    settings = get_settings()
    pairs: list[tuple[DocumentMediaKind, str]] = []
    for upload in files:
        result = await save_uploaded_file_auto(upload, settings=settings, strict_content_type=False)
        pairs.append((document_media_kind_from_upload(result.file_type), result.file_url))
    return pairs


@router.get(
    "",
    response_model=ApiResponse[list[CompanyDocumentAndFileRead]],
    summary="List documents & files for a company",
    description="Ordered by ``expiry_date`` (soonest first). Each item includes ``media``.",
)
def list_company_documents(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    items = _svc(db).list_for_owner(str(company_id), current["user_id"])
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [_dump_doc(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "",
    response_model=ApiResponse[CompanyDocumentAndFileRead],
    summary="Register a document / file record (multipart)",
    description=(
        "``multipart/form-data``: ``document_type``, ``expiry_date`` (ISO date), "
        "optional ``reminder_by_days``, optional repeated ``files``."
    ),
)
async def create_company_document(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
    document_type: Annotated[CompanyDocumentType, Form()],
    expiry_date: Annotated[str, Form(description="ISO-8601 date, e.g. 2026-12-31")],
    reminder_by_days: Annotated[str | None, Form()] = None,
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
        exp = date.fromisoformat(str(expiry_date).strip())
    except ValueError:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid expiry_date.")
    try:
        reminder = _parse_reminder(reminder_by_days)
    except ValueError:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid reminder_by_days.")
    try:
        data = CompanyDocumentAndFileCreate(
            document_type=document_type,
            expiry_date=exp,
            reminder_by_days=reminder,
        )
    except ValidationError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    try:
        if uploads:
            media_pairs = await _upload_pairs_for_documents(uploads)
            row = _svc(db).create_with_media_urls(str(company_id), current["user_id"], data, media_pairs)
        else:
            row = _svc(db).create(str(company_id), current["user_id"], data)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump_doc(row), message=ResponseEnum.SUCCESS.value)


@router.get(
    "/{document_id}",
    response_model=ApiResponse[CompanyDocumentAndFileRead],
    summary="Get one document & its media",
)
def get_company_document(
    company_id: UUID,
    document_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    row = _svc(db).get_for_owner(str(company_id), str(document_id), current["user_id"])
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_doc(row), message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/{document_id}",
    response_model=ApiResponse[CompanyDocumentAndFileRead],
    summary="Update a document record",
)
def update_company_document(
    company_id: UUID,
    document_id: UUID,
    data: CompanyDocumentAndFileUpdate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).update(str(company_id), str(document_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_doc(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{document_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete a document and its media",
)
def delete_company_document(
    company_id: UUID,
    document_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    ok = _svc(db).delete(str(company_id), str(document_id), current["user_id"])
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/{document_id}/media",
    response_model=ApiResponse[DocumentMediaRead],
    summary="Attach media (multipart file)",
    description="``multipart/form-data`` with a ``file`` part; maps to images / videos / files automatically.",
)
async def add_document_media(
    company_id: UUID,
    document_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
    file: Annotated[UploadFile, File(..., description="Image, video, or document")],
):
    settings = get_settings()
    try:
        result = await save_uploaded_file_auto(file, settings=settings, strict_content_type=False)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    kind = document_media_kind_from_upload(result.file_type)
    try:
        m = _svc(db).add_media(
            str(company_id),
            str(document_id),
            current["user_id"],
            DocumentMediaCreate(media_type=kind, media_link=result.file_url),
        )
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if m is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        DocumentMediaRead.model_validate(m).model_dump(mode="json"),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete(
    "/{document_id}/media/{media_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Remove one media row",
)
def delete_document_media(
    company_id: UUID,
    document_id: UUID,
    media_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    ok = _svc(db).delete_media(
        str(company_id), str(document_id), str(media_id), current["user_id"]
    )
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
