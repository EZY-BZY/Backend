"""Data access for industries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.industries.models import Industry


class IndustryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, industry_id: str) -> Industry | None:
        return self.db.get(Industry, industry_id)

    def create(self, row: Industry) -> Industry:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: Industry) -> Industry:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: Industry) -> None:
        self.db.delete(row)
        self.db.commit()

    def list_paginated(
        self,
        *,
        skip: int,
        limit: int,
    ) -> tuple[list[Industry], int]:
        base = select(Industry).order_by(Industry.created_at.desc())
        count_stmt = select(func.count()).select_from(base.subquery())
        total = self.db.execute(count_stmt).scalar_one()
        stmt = base.offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total
