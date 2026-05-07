"""
Clients — **company documents & files** (owner CRUD + documents_media).

**Base path:** ``/clients/companies/{company_id}/documents-and-files``.

**Auth:** Owner JWT. Each document row includes nested ``media`` (``documents_media``).
``media_type`` on media is one of: ``images``, ``videos``, ``files``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
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

router = APIRouter(
    prefix="/companies/{company_id}/documents-and-files",
    tags=["Company documents & files (clients)"],
)


def _svc(db: DbSession) -> CompanyDocumentAndFileService:
    return CompanyDocumentAndFileService(db)


def _dump_doc(row) -> dict:
    return CompanyDocumentAndFileRead.model_validate(row).model_dump(mode="json")


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
    summary="Register a document / file record",
)
def create_company_document(
    company_id: UUID,
    data: CompanyDocumentAndFileCreate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        row = _svc(db).create(str(company_id), current["user_id"], data)
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
    summary="Attach media to a document",
)
def add_document_media(
    company_id: UUID,
    document_id: UUID,
    data: DocumentMediaCreate,
    db: DbSession,
    current: CurrentOwnerRequired,
):
    try:
        m = _svc(db).add_media(str(company_id), str(document_id), current["user_id"], data)
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
