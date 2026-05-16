"""Cross-module validation helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.organisation_structure.repository import OrganisationStructureRepository


def ensure_organisation_structure_for_company(
    db: Session,
    company_id: str,
    organisation_structure_id: str | None,
) -> None:
    """Raise ``ValueError`` if the structure is missing, deleted, or belongs to another company."""
    if organisation_structure_id is None:
        return
    row = OrganisationStructureRepository(db).get_by_id(organisation_structure_id)
    if row is None or str(row.company_id) != str(company_id) or row.is_deleted:
        raise ValueError("Organisation structure not found for this company.")
