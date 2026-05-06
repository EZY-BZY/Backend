"""Beasy internal routes for managing company owners."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query

from app.common.allenums import OwnerAccountStatus, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.companies_owners.schemas import (
    CompanyOwnerAdminRead,
    OwnerStatusUpdateRequest,
    OwnersListFilters,
)
from app.modules.companies_owners.service import CompanyOwnerService

router = APIRouter(prefix="/owners", tags=["Owners (Beasy)"])


def _svc(db: DbSession) -> CompanyOwnerService:
    return CompanyOwnerService(db)


@router.get("", response_model=ApiResponse[list[CompanyOwnerAdminRead]])
def list_owners(
    db: DbSession,
    _: CurrentEmployeeRequired,
    account_status: OwnerAccountStatus | None = Query(None),
    is_verified_phone: bool | None = Query(None),
    join_date_from: datetime | None = Query(None),
    join_date_to: datetime | None = Query(None),
):
    items = _svc(db).list(
        OwnersListFilters(
            account_status=account_status,
            is_verified_phone=is_verified_phone,
            join_date_from=join_date_from,
            join_date_to=join_date_to,
        )
    )
    return json_success(
        [CompanyOwnerAdminRead.model_validate(i).model_dump() for i in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.get("/{owner_id}", response_model=ApiResponse[CompanyOwnerAdminRead])
def get_owner(owner_id: UUID, db: DbSession, _: CurrentEmployeeRequired):
    row = _svc(db).get_by_id(str(owner_id))
    if not row:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Owner not found")
    return json_success(
        CompanyOwnerAdminRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.get("/search", response_model=ApiResponse[list[CompanyOwnerAdminRead]])
def search_owners(db: DbSession, _: CurrentEmployeeRequired, query: str = Query(..., min_length=1)):
    items = _svc(db).search(query.strip())
    return json_success(
        [CompanyOwnerAdminRead.model_validate(i).model_dump() for i in items],
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch("/{owner_id}/status", response_model=ApiResponse[CompanyOwnerAdminRead])
def change_owner_status(
    owner_id: UUID,
    body: OwnerStatusUpdateRequest,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    row = _svc(db).set_status(owner_id=str(owner_id), status=body.account_status, actor_id=str(current.id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Owner not found")
    return json_success(
        CompanyOwnerAdminRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )

