"""Terms business logic: multiple rows per type, ordering, soft delete, version history."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.pagination import PaginationParams
from app.db.base import utc_now
from app.modules.terms.enums import HistoryAction, TermType
from app.modules.terms.models import Term, TermHistory
from app.modules.terms.repository import TermRepository
from app.modules.terms.schemas import TermCreate, TermUpdate


class TermService:
    """Terms CRUD with automatic terms_history version rows (full type snapshot)."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = TermRepository(db)

    def list_by_type_ordered(
        self,
        term_type: TermType,
        *,
        include_deleted: bool = False,
    ) -> list[Term]:
        return self._repo.list_by_type_ordered(term_type.value, include_deleted=include_deleted)

    def list_history_grouped_by_day(
        self,
        term_type: TermType,
        pagination: PaginationParams,
    ) -> tuple[list[tuple[datetime, list[TermHistory]]], int]:
        """
        Paginate by distinct UTC calendar days (newest first).
        Returns [(day_bucket_start, [TermHistory rows that day, newest first]), ...], total_days.
        """
        tv = term_type.value
        day_bucket = func.date_trunc("day", TermHistory.version_at).label("day")

        distinct_days = (
            select(day_bucket)
            .where(TermHistory.term_type == tv)
            .distinct()
            .order_by(day_bucket.desc())
        ).subquery()

        total_days = int(
            self._db.execute(select(func.count()).select_from(distinct_days)).scalar_one()
        )

        day_page = (
            select(distinct_days.c.day)
            .select_from(distinct_days)
            .order_by(distinct_days.c.day.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        day_values = list(self._db.execute(day_page).scalars().all())

        groups: list[tuple[datetime, list[TermHistory]]] = []
        for day_start in day_values:
            rows = list(
                self._db.execute(
                    select(TermHistory)
                    .where(TermHistory.term_type == tv)
                    .where(func.date_trunc("day", TermHistory.version_at) == day_start)
                    .order_by(TermHistory.version_at.desc())
                ).scalars().all()
            )
            groups.append((day_start, rows))
        return groups, total_days

    @staticmethod
    def _snapshot_items_from_terms(terms: list[Term], *, changed_term_id: str) -> list[dict]:
        return [
            {
                "name_en": t.name_en,
                "name_ar": t.name_ar,
                "name_fr": t.name_fr,
                "description_en": t.description_en,
                "description_ar": t.description_ar,
                "description_fr": t.description_fr,
                "type": t.term_type,
                "order": t.sort_order,
                "is_changed": t.id == changed_term_id,
            }
            for t in terms
        ]

    def _append_version_history(
        self,
        *,
        term_type_value: str,
        action: HistoryAction,
        actor_id: str,
        changed_term_id: str,
        snapshot_items: list[dict],
    ) -> None:
        row = TermHistory(
            term_type=term_type_value,
            action=action.value,
            performed_by=actor_id,
            version_at=utc_now(),
            changed_term_id=changed_term_id,
            terms_snapshot=snapshot_items,
        )
        self._repo.add(row)

    def create(self, data: TermCreate, actor_id: str) -> Term:
        next_order = self._repo.max_sort_order_for_type(data.type.value) + 1
        sort_order = data.order if data.order is not None else next_order
        term = Term(
            sort_order=sort_order,
            name_en=data.name_en,
            name_ar=data.name_ar,
            name_fr=data.name_fr,
            description_en=data.description_en,
            description_ar=data.description_ar,
            description_fr=data.description_fr,
            term_type=data.type.value,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self._repo.add(term)
        try:
            self._repo.flush()
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create term (constraint violation).") from e

        active = self._repo.list_by_type_ordered(term.term_type, include_deleted=False)
        snap = self._snapshot_items_from_terms(active, changed_term_id=term.id)
        self._append_version_history(
            term_type_value=term.term_type,
            action=HistoryAction.CREATED,
            actor_id=actor_id,
            changed_term_id=term.id,
            snapshot_items=snap,
        )
        self._repo.commit()
        self._repo.refresh(term)
        return term

    def update(self, term_id: str, data: TermUpdate, actor_id: str) -> Term:
        term = self._repo.get_by_id(term_id, include_deleted=False)
        if term is None:
            raise ValueError("Term not found or has been deleted.")

        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return term

        if data.name_en is not None:
            term.name_en = data.name_en
        if data.name_ar is not None:
            term.name_ar = data.name_ar
        if data.name_fr is not None:
            term.name_fr = data.name_fr
        if data.description_en is not None:
            term.description_en = data.description_en
        if data.description_ar is not None:
            term.description_ar = data.description_ar
        if data.description_fr is not None:
            term.description_fr = data.description_fr
        if data.order is not None:
            term.sort_order = data.order
        term.updated_by = actor_id

        self._repo.flush()
        active = self._repo.list_by_type_ordered(term.term_type, include_deleted=False)
        snap = self._snapshot_items_from_terms(active, changed_term_id=term.id)
        self._append_version_history(
            term_type_value=term.term_type,
            action=HistoryAction.UPDATED,
            actor_id=actor_id,
            changed_term_id=term.id,
            snapshot_items=snap,
        )
        self._repo.commit()
        self._repo.refresh(term)
        return term

    def soft_delete(self, term_id: str, actor_id: str) -> None:
        term = self._repo.get_by_id(term_id, include_deleted=False)
        if term is None:
            raise ValueError("Term not found or already deleted.")

        term_type_value = term.term_type
        changed_id = term.id
        term.deleted_at = datetime.now(timezone.utc)
        term.updated_by = actor_id
        self._repo.flush()

        active = self._repo.list_by_type_ordered(term_type_value, include_deleted=False)
        snap = self._snapshot_items_from_terms(active, changed_term_id=changed_id)
        if not any(item["is_changed"] for item in snap):
            snap.append(
                {
                    "name_en": term.name_en,
                    "name_ar": term.name_ar,
                    "name_fr": term.name_fr,
                    "description_en": term.description_en,
                    "description_ar": term.description_ar,
                    "description_fr": term.description_fr,
                    "type": term.term_type,
                    "order": term.sort_order,
                    "is_changed": True,
                }
            )
        self._append_version_history(
            term_type_value=term_type_value,
            action=HistoryAction.DELETED,
            actor_id=actor_id,
            changed_term_id=changed_id,
            snapshot_items=snap,
        )
        self._repo.commit()
