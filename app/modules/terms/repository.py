"""Data access for terms and terms_history."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.terms.models import Term, TermHistory


class TermRepository:
    """Repository for Term and TermHistory."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def max_sort_order_for_type(self, term_type: str) -> int:
        """Largest `order` among non-deleted terms of this type; 0 if none."""
        stmt = select(func.coalesce(func.max(Term.sort_order), 0)).where(
            Term.term_type == term_type,
            Term.deleted_at.is_(None),
        )
        return int(self.db.execute(stmt).scalar_one())

    def list_by_type_ordered(
        self,
        term_type: str,
        *,
        include_deleted: bool = False,
    ) -> list[Term]:
        """Terms for one type, ascending by `order` then id."""
        stmt = select(Term).where(Term.term_type == term_type)
        if not include_deleted:
            stmt = stmt.where(Term.deleted_at.is_(None))
        stmt = stmt.order_by(Term.sort_order.asc(), Term.id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, term_id: str, *, include_deleted: bool = False) -> Term | None:
        t = self.db.get(Term, term_id)
        if t is None:
            return None
        if not include_deleted and t.deleted_at is not None:
            return None
        return t

    def add(self, *objs: Term | TermHistory) -> None:
        for o in objs:
            self.db.add(o)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj: Term) -> None:
        self.db.refresh(obj)
