"""Public terms read routes (no authentication)."""

from fastapi import APIRouter

from app.common.api_response import ApiResponse, json_success
from app.common.allenums import ResponseEnum
from app.db.session import DbSession
from app.modules.terms.enums import TermType
from app.modules.terms.schemas import TermPublicRead
from app.modules.terms.service import TermService

router = APIRouter(prefix="/terms",)


def _service(db: DbSession) -> TermService:
    return TermService(db)


@router.get(
    "/{term_type}",
    response_model=ApiResponse[list[TermPublicRead]],
)
def list_active_terms_by_type(
    term_type: TermType,
    db: DbSession,
):
    """
    Active (non-deleted) terms for this type only, ascending by `order`.
    Public-safe: no ids, audit fields, or timestamps.
    """
    svc = _service(db)
    terms = svc.list_by_type_ordered(term_type, include_deleted=False)
    return json_success(
        [TermPublicRead.model_validate(t).model_dump() for t in terms],
        message=ResponseEnum.SUCCESS.value,
    )
