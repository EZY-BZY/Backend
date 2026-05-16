"""
Clients — **organisation structure** (departments) for one company.

**Base path:** ``/clients/companies/{company_id}/organisation-structure``

**Auth:** Company owner or company admin employee (same rules as employee management).

``total_employees`` and ``total_salaries`` are computed from assigned employees and cannot be set via API.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import Pagination
from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.pagination import pagination_pages
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.company_employees.dependencies import CurrentEmployerRequired
from app.modules.organisation_structure.schemas import (
    OrganisationStructureCreate,
    OrganisationStructureDetailRead,
    OrganisationStructurePaginatedList,
    OrganisationStructureRead,
    OrganisationStructureUpdate,
    organisation_structure_detail_dict,
)
from app.modules.organisation_structure.service import OrganisationStructureService

router = APIRouter(
    prefix="/companies/{company_id}/organisation-structure",
    tags=["Organisation structure (clients)"],
)


def _svc(db: DbSession) -> OrganisationStructureService:
    return OrganisationStructureService(db)


def _dump(row) -> dict:
    return OrganisationStructureRead.model_validate(row).model_dump(mode="json")


@router.post(
    "",
    response_model=ApiResponse[OrganisationStructureRead],
    summary="Create organisation structure",
)
def create_organisation_structure(
    company_id: UUID,
    data: OrganisationStructureCreate,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        row = _svc(db).create(str(company_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)


@router.get(
    "",
    response_model=ApiResponse[OrganisationStructurePaginatedList],
    summary="List organisation structures (paginated, searchable)",
    description=(
        "Paginated list with optional ``search`` on ``name_en`` or ``name_ar``. "
        "Non-deleted records appear first. "
        "``total_employees`` and ``total_salaries`` at the root are summed across all "
        "non-deleted departments in the company (not just the current page)."
    ),
)
def list_organisation_structures(
    company_id: UUID,
    db: DbSession,
    current: CurrentEmployerRequired,
    pagination: Pagination,
    search: str | None = Query(None, description="Filter by name_en or name_ar (case-insensitive)"),
):
    result = _svc(db).list_paginated(
        str(company_id),
        current,
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
    )
    if result is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    rows, departments_total, total_employees, total_salaries = result
    pages = pagination_pages(departments_total, pagination.page_size)
    payload = OrganisationStructurePaginatedList(
        items=[OrganisationStructureRead.model_validate(r) for r in rows],
        total=departments_total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
        total_employees=total_employees,
        total_salaries=total_salaries,
    ).model_dump(mode="json")
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@router.post(
    "/recalculate-totals",
    response_model=ApiResponse[MessageResponse],
    summary="Recalculate totals for all organisation structures in the company",
)
def recalculate_all_organisation_structure_totals(
    company_id: UUID,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        count = _svc(db).recalculate_all_for_company(str(company_id), current)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        MessageResponse(message=f"Recalculated totals for {count} organisation structure(s).").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{structure_id}",
    response_model=ApiResponse[OrganisationStructureDetailRead],
    summary="Get organisation structure by id with employees",
    description=(
        "Returns the organisation structure record and assigned employees "
        "(``id``, ``name``, ``role``, ``salary``, ``bonus_amount``, ``image``), "
        "non-deleted active employees first."
    ),
)
def get_organisation_structure(
    company_id: UUID,
    structure_id: UUID,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    result = _svc(db).get_by_id_with_employees(str(company_id), str(structure_id), current)
    if result is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    row, employees = result
    return json_success(
        organisation_structure_detail_dict(row, employees),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{structure_id}",
    response_model=ApiResponse[OrganisationStructureRead],
    summary="Update organisation structure",
    description="``total_employees`` and ``total_salaries`` cannot be updated via this endpoint.",
)
def update_organisation_structure(
    company_id: UUID,
    structure_id: UUID,
    data: OrganisationStructureUpdate,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        row = _svc(db).update(str(company_id), str(structure_id), current, data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)


@router.delete(
    "/{structure_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Soft-delete organisation structure",
    description="Fails if any employee is still assigned to this structure.",
)
def delete_organisation_structure(
    company_id: UUID,
    structure_id: UUID,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    try:
        ok = _svc(db).delete(str(company_id), str(structure_id), current)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(
        MessageResponse(message="Organisation structure marked as deleted").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/{structure_id}/recalculate-totals",
    response_model=ApiResponse[OrganisationStructureRead],
    summary="Recalculate totals for one organisation structure",
)
def recalculate_organisation_structure_totals(
    company_id: UUID,
    structure_id: UUID,
    db: DbSession,
    current: CurrentEmployerRequired,
):
    row = _svc(db).recalculate_totals(str(company_id), str(structure_id), current)
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump(row), message=ResponseEnum.SUCCESS.value)
