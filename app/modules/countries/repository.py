"""Data access for countries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.countries.models import Country


class CountryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, country_id: str) -> Country | None:
        return self.db.get(Country, country_id)

    def get_by_phone_code(self, phone_code: str) -> Country | None:
        stmt = select(Country).where(Country.phone_code == phone_code)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name_en(self, name_en: str) -> Country | None:
        stmt = select(Country).where(Country.name_en == name_en)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paginated(
        self,
        *,
        skip: int,
        limit: int,
    ) -> tuple[list[Country], int]:
        base = select(Country).order_by(Country.name_en.asc())
        count_stmt = select(func.count()).select_from(base.subquery())
        total = self.db.execute(count_stmt).scalar_one()
        stmt = base.offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def create(self, row: Country) -> Country:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: Country) -> Country:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: Country) -> None:
        self.db.delete(row)
        self.db.commit()

