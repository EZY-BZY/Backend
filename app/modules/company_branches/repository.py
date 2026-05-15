"""Data access for company_branches and related rows."""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.common.allenums import Weekday
from app.modules.company_branches.models import (
    CompanyBranch,
    CompanyBranchContact,
    CompanyBranchWorkingHours,
)


_WEEKDAY_ORDER = (
    "saturday",
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
)


def _weekday_sort_key(day: str) -> int:
    try:
        return _WEEKDAY_ORDER.index(day)
    except ValueError:
        return 99


class CompanyBranchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _branch_load_options(self):
        return (
            selectinload(CompanyBranch.contacts),
            selectinload(CompanyBranch.working_hours),
        )

    def get_branch(self, branch_id: str, *, load_children: bool = False) -> CompanyBranch | None:
        if not load_children:
            return self.db.get(CompanyBranch, branch_id)
        stmt = (
            select(CompanyBranch)
            .where(CompanyBranch.id == branch_id)
            .options(*self._branch_load_options())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_company(self, company_id: str, *, load_children: bool = False) -> list[CompanyBranch]:
        stmt = select(CompanyBranch).where(CompanyBranch.company_id == company_id)
        if load_children:
            stmt = stmt.options(*self._branch_load_options())
        stmt = stmt.order_by(CompanyBranch.branch_name.asc())
        rows = list(self.db.execute(stmt).scalars().all())
        self._sort_working_hours(rows)
        return rows

    def list_for_company_paginated(
        self,
        company_id: str,
        *,
        skip: int,
        limit: int,
        load_children: bool = False,
        visible_to_public_only: bool = False,
    ) -> tuple[list[CompanyBranch], int]:
        base = select(CompanyBranch).where(CompanyBranch.company_id == company_id)
        if visible_to_public_only:
            base = base.where(
                CompanyBranch.is_active.is_(True),
                CompanyBranch.is_visible_to_clients.is_(True),
            )
        if load_children:
            base = base.options(*self._branch_load_options())

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int(self.db.execute(count_stmt).scalar_one())

        stmt = base.order_by(CompanyBranch.branch_name.asc()).offset(skip).limit(limit)
        rows = list(self.db.execute(stmt).scalars().all())
        self._sort_working_hours(rows)
        return rows, total

    def list_filtered(
        self,
        *,
        company_id: str | None = None,
        branch_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[CompanyBranch]:
        stmt = select(CompanyBranch).options(*self._branch_load_options())
        if company_id is not None:
            stmt = stmt.where(CompanyBranch.company_id == company_id)
        if branch_type is not None:
            stmt = stmt.where(CompanyBranch.branch_type == branch_type)
        if is_active is not None:
            stmt = stmt.where(CompanyBranch.is_active == is_active)
        stmt = stmt.order_by(CompanyBranch.company_id.asc(), CompanyBranch.branch_name.asc())
        rows = list(self.db.execute(stmt).scalars().all())
        self._sort_working_hours(rows)
        return rows

    def _sort_working_hours(self, branches: list[CompanyBranch]) -> None:
        for b in branches:
            b.working_hours.sort(key=lambda w: _weekday_sort_key(w.day_of_week))

    def create_branch_with_default_schedule(self, row: CompanyBranch, *, actor_id: str) -> CompanyBranch:
        """Persist branch and seed seven weekday rows (all day off) in one transaction."""
        self.db.add(row)
        self.db.flush()
        for day in Weekday:
            self.db.add(
                CompanyBranchWorkingHours(
                    branch_id=row.id,
                    day_of_week=day.value,
                    is_day_off=True,
                    opening_time=None,
                    closing_time=None,
                    is_active=True,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_branch(self, row: CompanyBranch) -> CompanyBranch:
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_contact(self, contact_id: str) -> CompanyBranchContact | None:
        return self.db.get(CompanyBranchContact, contact_id)

    def create_contact(self, row: CompanyBranchContact) -> CompanyBranchContact:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_contact(self, row: CompanyBranchContact) -> CompanyBranchContact:
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_working_hour(self, branch_id: str, day: str) -> CompanyBranchWorkingHours | None:
        stmt = select(CompanyBranchWorkingHours).where(
            CompanyBranchWorkingHours.branch_id == branch_id,
            CompanyBranchWorkingHours.day_of_week == day,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_working_hour_by_id(self, wh_id: str) -> CompanyBranchWorkingHours | None:
        return self.db.get(CompanyBranchWorkingHours, wh_id)

    def create_working_hour(self, row: CompanyBranchWorkingHours) -> CompanyBranchWorkingHours:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_working_hour(self, row: CompanyBranchWorkingHours) -> CompanyBranchWorkingHours:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_working_hour_row(self, row: CompanyBranchWorkingHours) -> None:
        self.db.delete(row)
        self.db.commit()

    def clear_primary_contacts(self, branch_id: str, *, except_contact_id: str | None = None) -> None:
        """Unset primary flag; does not commit (caller commits with related changes)."""
        stmt = update(CompanyBranchContact).where(CompanyBranchContact.branch_id == branch_id)
        if except_contact_id is not None:
            stmt = stmt.where(CompanyBranchContact.id != except_contact_id)
        stmt = stmt.values(is_primary=False)
        self.db.execute(stmt)
