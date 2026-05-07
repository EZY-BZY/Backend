"""
Beasy — read **fixed assets** for a company (same scope as owner app).

**Base path:** ``/beasy/companies/{company_id}/fixed-assets``

**Auth:** Beasy employee JWT.

**OpenAPI:** Item title ``CompanyFixedAsset``; each asset includes nested ``media``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.fixed_assets.schemas import FixedAssetBeasyRead
from app.modules.fixed_assets.service import FixedAssetService

router = APIRouter(
    prefix="/companies/{company_id}/fixed-assets",
    tags=["Fixed assets (Beasy) Ignore for now"],
)


def _svc(db: DbSession) -> FixedAssetService:
    return FixedAssetService(db)


def _dump_asset(row) -> dict:
    return FixedAssetBeasyRead.model_validate(row).model_dump(by_alias=True, mode="json")


@router.get(
    "",
    response_model=ApiResponse[list[FixedAssetBeasyRead]],
    summary="List a company's fixed assets",
    description="404 if ``company_id`` does not exist. Each row includes ``media`` from ``assets_media``.",
)
def list_company_fixed_assets(
    company_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    items = _svc(db).list_for_company_admin(str(company_id))
    if items is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Company not found")
    return json_success(
        [_dump_asset(x) for x in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get(
    "/{asset_id}",
    response_model=ApiResponse[FixedAssetBeasyRead],
    summary="Get one fixed asset for this company",
)
def get_company_fixed_asset(
    company_id: UUID,
    asset_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    row = _svc(db).get_for_company_admin(str(company_id), str(asset_id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Not found")
    return json_success(_dump_asset(row), message=ResponseEnum.SUCCESS.value)
