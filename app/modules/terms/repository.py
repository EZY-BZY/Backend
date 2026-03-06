"""Data access for terms."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.terms.models import Term


class TermRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, term_id: UUID | str) -> Term | None:
        return self.db.get(Term, str(term_id))

    def create(self, term: Term) -> Term:
        self.db.add(term)
        self.db.commit()
        self.db.refresh(term)
        return term

    def update(self, term: Term) -> Term:
        self.db.commit()
        self.db.refresh(term)
        return term

    def delete(self, term: Term) -> None:
        self.db.delete(term)
        self.db.commit()

    def list_terms(
        self,
        *,
        term_type: str | None = None,
        status: str | None = None,
        order_by_order: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Term], int]:
        """List terms with optional filters. Returns (items, total)."""
        base = select(Term)
        if term_type:
            base = base.where(Term.term_type == term_type)
        if status:
            base = base.where(Term.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        if order_by_order:
            base = base.order_by(Term.term_order.asc(), Term.created_at.asc())
        else:
            base = base.order_by(Term.created_at.desc())
        base = base.offset(skip).limit(limit)
        items = list(self.db.execute(base).scalars().all())
        return items, total
