"""Beasy employees: countries CUD."""

from uuid import UUID

from fastapi import APIRouter
from app.common.api_response import json_error, json_success

from app.common.api_response import ApiResponse
from app.common.allenums import ResponseEnum
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.countries.schemas import CountryCreate, CountryRead, CountryUpdate
from app.modules.countries.service import CountryService

router = APIRouter(prefix="/countries", tags=["Countries (Beasy)"])


def _svc(db: DbSession) -> CountryService:
    return CountryService(db)


@router.post("", response_model=ApiResponse[CountryRead])
def create_country(
    data: CountryCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    svc = _svc(db)
    try:
        row = svc.create(data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        CountryRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch("/{country_id}", response_model=ApiResponse[CountryRead])
def update_country(
    country_id: UUID,
    data: CountryUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    svc = _svc(db)
    try:
        row = svc.update(str(country_id), data, actor_id=str(current.id))
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Country not found")
    return json_success(
        CountryRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete("/{country_id}", response_model=ApiResponse[MessageResponse])
def delete_country(
    country_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    ok = _svc(db).delete(str(country_id))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Country not found")
    return json_success(
        MessageResponse(message="Country deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )

