"""Business logic for company branches, contacts, and working hours."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.allenums import Weekday
from app.modules.companies.service import CompanyService
from app.modules.company_branches.dependencies import ensure_client_company_access, is_company_insider
from app.modules.company_branches.models import CompanyBranch, CompanyBranchContact, CompanyBranchWorkingHours
from app.modules.company_branches.repository import CompanyBranchRepository
from app.modules.company_branches.schemas import (
    CompanyBranchContactCreate,
    CompanyBranchContactUpdate,
    CompanyBranchCreate,
    CompanyBranchUpdate,
    CompanyBranchWorkingHoursPut,
)
from app.modules.clients_auth.dependencies import CurrentClient


_WEEK_ORDER = list(Weekday)


def _sort_hours(rows: list[CompanyBranchWorkingHours]) -> list[CompanyBranchWorkingHours]:
    return sorted(rows, key=lambda w: _WEEK_ORDER.index(Weekday(w.day_of_week)))


class CompanyBranchService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyBranchRepository(db)

    def _ensure_access(self, current: CurrentClient, company_id: str) -> None:
        ensure_client_company_access(self._db, current, company_id)

    def _get_branch_for_company(self, company_id: str, branch_id: str, *, load_children: bool) -> CompanyBranch | None:
        row = self._repo.get_branch(branch_id, load_children=load_children)
        if row is None or row.company_id != company_id:
            return None
        return row

    def create_branch(
        self,
        company_id: str,
        current: CurrentClient,
        data: CompanyBranchCreate,
    ) -> CompanyBranch:
        self._ensure_access(current, company_id)
        actor = current["user_id"]
        row = CompanyBranch(
            company_id=company_id,
            branch_name=data.branch_name,
            branch_location_description=data.branch_location_description,
            latitude=data.latitude,
            longitude=data.longitude,
            branch_type=data.branch_type.value,
            is_active=True,
            is_visible_to_clients=data.is_visible_to_clients,
            created_by=actor,
            updated_by=actor,
        )
        try:
            return self._repo.create_branch_with_default_schedule(row, actor_id=actor)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create branch.") from e

    def list_branches_client(self, company_id: str, current: CurrentClient) -> list[CompanyBranch]:
        self._ensure_access(current, company_id)
        return self._repo.list_for_company(company_id, load_children=True)

    def list_branches_client_paginated(
        self,
        company_id: str,
        current: CurrentClient | None,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[CompanyBranch], int] | None:
        """
        Paginated branches for a company.

        Insiders (owner / company employee): all branches.
        Public: only ``is_active`` and ``is_visible_to_clients`` both true.
        """
        if CompanyService(self._db).get_company_by_id(company_id) is None:
            return None
        insider = is_company_insider(self._db, current, company_id)
        if insider and current is not None:
            self._ensure_access(current, company_id)
        skip = (page - 1) * page_size
        items, total = self._repo.list_for_company_paginated(
            company_id,
            skip=skip,
            limit=page_size,
            load_children=True,
            visible_to_public_only=not insider,
        )
        return items, total

    def get_branch_client(
        self,
        company_id: str,
        branch_id: str,
        current: CurrentClient | None,
    ) -> CompanyBranch | None:
        if CompanyService(self._db).get_company_by_id(company_id) is None:
            return None
        insider = is_company_insider(self._db, current, company_id)
        if insider and current is not None:
            self._ensure_access(current, company_id)
        row = self._get_branch_for_company(company_id, branch_id, load_children=True)
        if row is None:
            return None
        if not insider and (not row.is_active or not row.is_visible_to_clients):
            return None
        return row

    def update_branch(
        self,
        company_id: str,
        branch_id: str,
        current: CurrentClient,
        data: CompanyBranchUpdate,
    ) -> CompanyBranch | None:
        self._ensure_access(current, company_id)
        row = self._get_branch_for_company(company_id, branch_id, load_children=False)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self._repo.get_branch(branch_id, load_children=True)
        if "branch_type" in payload and payload["branch_type"] is not None:
            row.branch_type = payload["branch_type"].value
            del payload["branch_type"]
        actor = current["user_id"]
        row.updated_by = actor
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            self._repo.save_branch(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update branch.") from e
        return self._repo.get_branch(branch_id, load_children=True)

    def deactivate_branch(self, company_id: str, branch_id: str, current: CurrentClient) -> bool:
        self._ensure_access(current, company_id)
        row = self._get_branch_for_company(company_id, branch_id, load_children=True)
        if row is None:
            return False
        actor = current["user_id"]
        row.is_active = False
        row.updated_by = actor
        for c in row.contacts:
            c.is_active = False
            c.is_primary = False
            c.updated_by = actor
        for wh in row.working_hours:
            wh.is_active = False
            wh.updated_by = actor
        try:
            self._repo.save_branch(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not deactivate branch.") from e
        return True

    def add_contact(
        self,
        company_id: str,
        branch_id: str,
        current: CurrentClient,
        data: CompanyBranchContactCreate,
    ) -> CompanyBranchContact:
        self._ensure_access(current, company_id)
        if self._get_branch_for_company(company_id, branch_id, load_children=False) is None:
            raise ValueError("Branch not found.")
        actor = current["user_id"]
        if data.is_primary:
            self._repo.clear_primary_contacts(branch_id, except_contact_id=None)
        row = CompanyBranchContact(
            branch_id=branch_id,
            contact_name=data.contact_name,
            phone_number=data.phone_number,
            is_primary=data.is_primary,
            is_active=True,
            created_by=actor,
            updated_by=actor,
        )
        self._db.add(row)
        try:
            self._db.commit()
            self._db.refresh(row)
        except IntegrityError as e:
            self._db.rollback()
            if "uq_company_branch_contacts_one_primary_active" in str(e.orig):
                raise ValueError("Only one primary active contact is allowed per branch.") from e
            raise ValueError("Could not create contact.") from e
        return row

    def update_contact(
        self,
        company_id: str,
        branch_id: str,
        contact_id: str,
        current: CurrentClient,
        data: CompanyBranchContactUpdate,
    ) -> CompanyBranchContact | None:
        self._ensure_access(current, company_id)
        if self._get_branch_for_company(company_id, branch_id, load_children=False) is None:
            return None
        row = self._repo.get_contact(contact_id)
        if row is None or row.branch_id != branch_id:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row
        if payload.get("is_active") is False:
            payload["is_primary"] = False
        if payload.get("is_primary") is True:
            self._repo.clear_primary_contacts(branch_id, except_contact_id=contact_id)
        actor = current["user_id"]
        row.updated_by = actor
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            return self._repo.save_contact(row)
        except IntegrityError as e:
            self._db.rollback()
            if "uq_company_branch_contacts_one_primary_active" in str(e.orig):
                raise ValueError("Only one primary active contact is allowed per branch.") from e
            raise ValueError("Could not update contact.") from e

    def deactivate_contact(self, company_id: str, branch_id: str, contact_id: str, current: CurrentClient) -> bool:
        self._ensure_access(current, company_id)
        if self._get_branch_for_company(company_id, branch_id, load_children=False) is None:
            return False
        row = self._repo.get_contact(contact_id)
        if row is None or row.branch_id != branch_id:
            return False
        row.is_active = False
        row.is_primary = False
        row.updated_by = current["user_id"]
        try:
            self._repo.save_contact(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not deactivate contact.") from e
        return True

    def put_working_hours(
        self,
        company_id: str,
        branch_id: str,
        current: CurrentClient,
        data: CompanyBranchWorkingHoursPut,
    ) -> list[CompanyBranchWorkingHours]:
        self._ensure_access(current, company_id)
        if self._get_branch_for_company(company_id, branch_id, load_children=False) is None:
            raise ValueError("Branch not found.")
        actor = current["user_id"]

        try:
            for item in data.hours:
                day_val = item.day_of_week.value
                existing = self._repo.get_working_hour(branch_id, day_val)
                if existing is None:
                    wh = CompanyBranchWorkingHours(
                        branch_id=branch_id,
                        day_of_week=day_val,
                        is_day_off=item.is_day_off,
                        opening_time=item.opening_time,
                        closing_time=item.closing_time,
                        is_active=True,
                        created_by=actor,
                        updated_by=actor,
                    )
                    self._db.add(wh)
                else:
                    existing.is_day_off = item.is_day_off
                    existing.opening_time = item.opening_time
                    existing.closing_time = item.closing_time
                    existing.is_active = True
                    existing.updated_by = actor
            self._db.commit()
        except IntegrityError as e:
            self._db.rollback()
            if "uq_company_branch_working_hours_branch_day" in str(e.orig):
                raise ValueError("Duplicate day in request or database conflict.") from e
            raise ValueError("Could not save working hours.") from e

        branch = self._repo.get_branch(branch_id, load_children=True)
        assert branch is not None
        return _sort_hours(list(branch.working_hours))

    def get_working_hours_client(
        self,
        company_id: str,
        branch_id: str,
        current: CurrentClient,
    ) -> list[CompanyBranchWorkingHours] | None:
        self._ensure_access(current, company_id)
        branch = self._get_branch_for_company(company_id, branch_id, load_children=True)
        if branch is None:
            return None
        return _sort_hours(list(branch.working_hours))

    def list_branches_beasy(
        self,
        *,
        company_id: str | None,
        branch_type: str | None,
        is_active: bool | None,
    ) -> list[CompanyBranch]:
        return self._repo.list_filtered(
            company_id=company_id,
            branch_type=branch_type,
            is_active=is_active,
        )

    def get_branch_beasy(self, branch_id: str) -> CompanyBranch | None:
        return self._repo.get_branch(branch_id, load_children=True)
