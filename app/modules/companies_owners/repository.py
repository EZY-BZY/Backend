"""Data access for company owners."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.common.allenums import OwnerAccountStatus
from app.modules.companies_owners.models import CompanyOwner


class CompanyOwnerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, owner_id: str) -> CompanyOwner | None:
        return self.db.get(CompanyOwner, owner_id)

    def get_by_phone(self, phone: str) -> CompanyOwner | None:
        stmt = select(CompanyOwner).where(CompanyOwner.phone == phone)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, row: CompanyOwner) -> CompanyOwner:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: CompanyOwner) -> CompanyOwner:
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_filtered(
        self,
        *,
        account_status: OwnerAccountStatus | None,
        is_verified_phone: bool | None,
        join_date_from: datetime | None,
        join_date_to: datetime | None,
    ) -> list[CompanyOwner]:
        stmt = select(CompanyOwner)

        clauses = []
        if account_status is not None:
            clauses.append(CompanyOwner.account_status == account_status.value)
        if is_verified_phone is not None:
            clauses.append(CompanyOwner.is_verified_phone == is_verified_phone)
        if join_date_from is not None:
            clauses.append(CompanyOwner.join_date >= join_date_from)
        if join_date_to is not None:
            clauses.append(CompanyOwner.join_date <= join_date_to)
        if clauses:
            stmt = stmt.where(and_(*clauses))

        stmt = stmt.order_by(CompanyOwner.join_date.desc())
        return list(self.db.execute(stmt).scalars().all())

    def search(self, query: str, *, owner_id: str | None) -> list[CompanyOwner]:
        if owner_id:
            row = self.get_by_id(owner_id)
            return [row] if row else []

        like = f"%{query}%"
        stmt = select(CompanyOwner).where(
            or_(
                CompanyOwner.name.ilike(like),
                CompanyOwner.phone.ilike(like),
            )
        )
        stmt = stmt.order_by(func.length(CompanyOwner.phone).asc(), CompanyOwner.join_date.desc())
        return list(self.db.execute(stmt).scalars().all())

