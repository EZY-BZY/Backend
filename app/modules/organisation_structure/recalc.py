"""Recompute denormalised totals on organisation structure rows."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.organisation_structure.repository import OrganisationStructureRepository


def refresh_organisation_structure_totals(db: Session, *structure_ids: str | None) -> None:
    """Recompute totals for each distinct non-empty structure id."""
    repo = OrganisationStructureRepository(db)
    seen: set[str] = set()
    for raw in structure_ids:
        if not raw:
            continue
        sid = str(raw)
        if sid in seen:
            continue
        seen.add(sid)
        repo.recompute_and_save_totals(sid, commit=False)
