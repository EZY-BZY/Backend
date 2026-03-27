"""Terms and conditions API. Permission-protected: manage_terms or add_term/edit_term/delete_term."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.common.pagination import pagination_pages
from app.common.schemas import MessageResponse, PaginatedResponse
from app.modules.employees.dependencies import CurrentEmployeeRequired, require_permission
from app.modules.terms.enums import TermStatus, TermType
from app.modules.terms.schemas import TermCreate, TermRead, TermReadByLanguage, TermUpdate
from app.db.session import DbSession
from app.modules.terms.service import TermService

router = APIRouter(prefix="/terms", tags=["organization-terms"])


def _get_service(db: DbSession) -> TermService:
    return TermService(db)


@router.post(
    "",
    response_model=TermRead,
    dependencies=[Depends(require_permission("manage_terms"))],
)
def add_term(
    data: TermCreate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Add a term. Requires manage_terms (or add_term) permission."""
    service = _get_service(db)
    term = service.create(data, created_by_id=current.id)
    return _term_to_read(term)


@router.patch(
    "/{term_id}",
    response_model=TermRead,
    dependencies=[Depends(require_permission("manage_terms"))],
)
def edit_term(
    term_id: UUID,
    data: TermUpdate,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Edit a term. Requires manage_terms (or edit_term) permission."""
    service = _get_service(db)
    term = service.update(term_id, data, updated_by_id=current.id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return _term_to_read(term)


@router.delete(
    "/{term_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("manage_terms"))],
)
def delete_term(
    term_id: UUID,
    db: DbSession,
    current: CurrentEmployeeRequired,
):
    """Delete a term. Requires manage_terms (or delete_term) permission."""
    service = _get_service(db)
    if not service.delete(term_id):
        raise HTTPException(status_code=404, detail="Term not found")
    return MessageResponse(message="Term deleted successfully")


@router.get("/{term_id}", response_model=TermRead)
def view_term(
    term_id: UUID,
    db: DbSession,
):
    """View single term. Public or require view_terms depending on policy."""
    service = _get_service(db)
    term = service.get_by_id(term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return _term_to_read(term)


@router.get(
    "",
    response_model=PaginatedResponse[TermRead],
)
def list_terms(
    db: DbSession,
    term_type: TermType | None = Query(None),
    status: TermStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all terms. Filter by type and status. Sorted by term_order by default.
    """
    service = _get_service(db)
    items, total = service.list_terms(
        term_type=term_type.value if term_type else None,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
    )
    pages = pagination_pages(total, page_size)
    return PaginatedResponse(
        items=[_term_to_read(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{term_id}/by-language",
    response_model=TermReadByLanguage,
)
def get_term_by_language(
    term_id: UUID,
    db: DbSession,
    lang: str = Query(..., pattern="^(ar|en|fr)$"),
):
    """Get term content for a specific language (ar, en, fr)."""
    service = _get_service(db)
    term = service.get_by_id(term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    if lang == "ar":
        title, desc = term.term_title_ar, term.term_desc_ar
    elif lang == "en":
        title, desc = term.term_title_en, term.term_desc_en
    else:
        title, desc = term.term_title_fr, term.term_desc_fr
    return TermReadByLanguage(
        id=UUID(term.id),
        title=title,
        description=desc,
        term_order=term.term_order,
        term_type=term.term_type,
        status=term.status,
        created_at=term.created_at,
        updated_at=term.updated_at,
    )


def _term_to_read(t) -> TermRead:
    return TermRead(
        id=UUID(t.id),
        term_title_ar=t.term_title_ar,
        term_title_en=t.term_title_en,
        term_title_fr=t.term_title_fr,
        term_desc_ar=t.term_desc_ar,
        term_desc_en=t.term_desc_en,
        term_desc_fr=t.term_desc_fr,
        term_order=t.term_order,
        term_type=TermType(t.term_type),
        status=TermStatus(t.status),
        created_at=t.created_at,
        updated_at=t.updated_at,
        created_by_id=UUID(t.created_by_id) if t.created_by_id else None,
        updated_by_id=UUID(t.updated_by_id) if t.updated_by_id else None,
    )
