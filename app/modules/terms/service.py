"""Business logic for terms and conditions."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.terms.models import Term
from app.modules.terms.repository import TermRepository
from app.modules.terms.schemas import TermCreate, TermUpdate


class TermService:
    def __init__(self, db: Session) -> None:
        self._repo = TermRepository(db)

    def get_by_id(self, term_id: UUID | str) -> Term | None:
        return self._repo.get_by_id(term_id)

    def create(
        self,
        data: TermCreate,
        created_by_id: UUID | str | None,
    ) -> Term:
        term = Term(
            term_title_ar=data.term_title_ar,
            term_title_en=data.term_title_en,
            term_title_fr=data.term_title_fr,
            term_desc_ar=data.term_desc_ar,
            term_desc_en=data.term_desc_en,
            term_desc_fr=data.term_desc_fr,
            term_order=data.term_order,
            term_type=data.term_type.value,
            status=data.status.value,
            created_by_id=str(created_by_id) if created_by_id else None,
            updated_by_id=str(created_by_id) if created_by_id else None,
        )
        return self._repo.create(term)

    def update(
        self,
        term_id: UUID | str,
        data: TermUpdate,
        updated_by_id: UUID | str | None,
    ) -> Term | None:
        term = self._repo.get_by_id(term_id)
        if not term:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(value, "value"):  # Enum
                setattr(term, key, value.value)
            else:
                setattr(term, key, value)
        term.updated_by_id = str(updated_by_id) if updated_by_id else None
        return self._repo.update(term)

    def delete(self, term_id: UUID | str) -> bool:
        term = self._repo.get_by_id(term_id)
        if not term:
            return False
        self._repo.delete(term)
        return True

    def list_terms(
        self,
        *,
        term_type: str | None = None,
        status: str | None = None,
        order_by_order: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Term], int]:
        skip = (page - 1) * page_size
        return self._repo.list_terms(
            term_type=term_type,
            status=status,
            order_by_order=order_by_order,
            skip=skip,
            limit=page_size,
        )
