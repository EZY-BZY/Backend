"""Beasy employees: industries CUD."""

from uuid import UUID

from fastapi import APIRouter

from app.common.api_response import ApiResponse, json_error, json_success
from app.common.allenums import ResponseEnum
from app.common.schemas import MessageResponse
from app.db.session import DbSession
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.industries.schemas import IndustryCreate, IndustryRead, IndustryUpdate
from app.modules.industries.service import IndustryService

router = APIRouter(prefix="/industries", tags=["Industries (Beasy)"])


def _svc(db: DbSession) -> IndustryService:
    return IndustryService(db)


@router.post("", response_model=ApiResponse[IndustryRead])
def create_industry(
    data: IndustryCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    row = _svc(db).create(data, actor_id=str(current.id))
    return json_success(
        IndustryRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.patch("/{industry_id}", response_model=ApiResponse[IndustryRead])
def update_industry(
    industry_id: UUID,
    data: IndustryUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    row = _svc(db).update(str(industry_id), data, actor_id=str(current.id))
    if row is None:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Industry not found")
    return json_success(
        IndustryRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.delete("/{industry_id}", response_model=ApiResponse[MessageResponse])
def delete_industry(
    industry_id: UUID,
    db: DbSession,
    _: CurrentEmployeeRequired,
):
    ok = _svc(db).delete(str(industry_id))
    if not ok:
        return json_error(ResponseEnum.ERROR.value, http_status=404, details="Industry not found")
    return json_success(
        MessageResponse(message="Industry deleted successfully").model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )
