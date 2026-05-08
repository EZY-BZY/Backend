"""Client (owner): create, read, update, deactivate company + visibility toggles."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.companies.schemas import (
    CompanyChangeVisibilityBody,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    company_read_dict,
)
from app.modules.companies.service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies (clients)"])


def _svc(db: DbSession) -> CompanyService:
    return CompanyService(db)


@router.post(
    "",
    response_model=ApiResponse[CompanyRead],
    summary="Create company",
    description=(
        "Create a company for the authenticated owner.\n\n"
        "Allowed on create:\n"
        "- `company_name_ar` (required)\n"
        "- `company_name_en` (optional)\n"
        "- `company_description_ar` (required)\n"
        "- `company_description_en` (optional)\n"
        "- `current_balance` (required)\n"
        "- `service` (required): services | products | products_and_services\n"
        "- `tax_number` (optional)\n"
        "- `image` (optional)\n"
        "- `industry_ids` (optional): list of industry UUIDs this company serves\n\n"
        "Show flags default to false; use `PUT .../change-statuses` to update them."
    ),
)
def create_company(db: DbSession, current: CurrentOwnerRequired, data: CompanyCreate):
    svc = _svc(db)
    try:
        row = svc.create_company(current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        company_read_dict(row, svc.industry_ids_for_company(str(row.id))),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{company_id}",
    response_model=ApiResponse[CompanyRead],
    summary="Get company details",
)
def get_company(company_id: UUID, db: DbSession, current: CurrentOwnerRequired):
    svc = _svc(db)
    row = svc.get_company(str(company_id), current["user_id"])
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        company_read_dict(row, svc.industry_ids_for_company(str(company_id))),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{company_id}",
    response_model=ApiResponse[CompanyRead],
    summary="Update company",
)
def update_company(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
    data: CompanyUpdate,
):
    svc = _svc(db)
    try:
        row = svc.update_company(str(company_id), current["user_id"], data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        company_read_dict(row, svc.industry_ids_for_company(str(company_id))),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch(
    "/{company_id}/deactivate",
    response_model=ApiResponse[MessageResponse],
    summary="Deactivate company",
    description="Sets company `status` to `inactive`.",
)
def deactivate_company(company_id: UUID, db: DbSession, current: CurrentOwnerRequired):
    row = _svc(db).deactivate_company(str(company_id), current["user_id"])
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        MessageResponse(message="Company deactivated").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.put(
    "/{company_id}/change-statuses",
    response_model=ApiResponse[CompanyRead],
    summary="Update visibility flags",
    description=(
        "Sets the four “show” toggles in one request:\n"
        "- `show_products`\n"
        "- `show_social_media`\n"
        "- `show_contact_info`\n"
        "- `show_branches`"
    ),
)
def change_company_visibility(
    company_id: UUID,
    db: DbSession,
    current: CurrentOwnerRequired,
    body: CompanyChangeVisibilityBody,
):
    svc = _svc(db)
    row = svc.change_company_visibility(str(company_id), current["user_id"], body)
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        company_read_dict(row, svc.industry_ids_for_company(str(company_id))),
        message=ResponseEnum.SUCCESS.value,
    )
