"""
Beasy — read **company documents & files** for a company.

**Base path:** ``/beasy/companies/{company_id}/documents-and-files``

**Auth:** Beasy employee JWT. Response title ``CompanyDocumentAndFile`` in OpenAPI.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.company_documents_and_files.schemas import CompanyDocumentAndFileBeasyRead
from app.modules.company_documents_and_files.service import CompanyDocumentAndFileService

router = APIRouter(
    prefix="/companies/{company_id}/documents-and-files",
    tags=["Company documents & files (Beasy)"],
)


def _svc(db: DbSession) -> CompanyDocumentAndFileService:
    return CompanyDocumentAndFileService(db)


def _dump_doc(row) -> dict:
    return CompanyDocumentAndFileBeasyRead.model_validate(row).model_dump(mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[CompanyDocumentAndFileBeasyRead]],
    summary="List a company's documents & files",
)
def list_company_documents_beasy(
    company_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    items = _svc(db).list_for_company_admin(str(company_id))
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [_dump_doc(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{document_id}",
    response_model=ApiResponse[CompanyDocumentAndFileBeasyRead],
    summary="Get one document & its media",
)
def get_company_document_beasy(
    company_id: UUID,
    document_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    row = _svc(db).get_for_company_admin(str(company_id), str(document_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_doc(row), message=ResponseEnum.SUCCESS.value)
