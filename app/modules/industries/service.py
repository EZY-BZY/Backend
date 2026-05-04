"""Industry CRUD."""

from sqlalchemy.orm import Session

from app.modules.industries.models import Industry
from app.modules.industries.repository import IndustryRepository
from app.modules.industries.schemas import IndustryCreate, IndustryUpdate


class IndustryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = IndustryRepository(db)

    def get_by_id(self, industry_id: str) -> Industry | None:
        return self._repo.get_by_id(industry_id)

    def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Industry], int]:
        skip = (page - 1) * page_size
        return self._repo.list_paginated(skip=skip, limit=page_size)

    def create(self, data: IndustryCreate, actor_id: str) -> Industry:
        row = Industry(
            name_en=data.name_en,
            name_ar=data.name_ar,
            name_fr=data.name_fr,
            image=data.image,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return self._repo.create(row)

    def update(self, industry_id: str, data: IndustryUpdate, actor_id: str) -> Industry | None:
        row = self._repo.get_by_id(industry_id)
        if row is None:
            return None
        if data.name_en is not None:
            row.name_en = data.name_en
        if data.name_ar is not None:
            row.name_ar = data.name_ar
        if data.name_fr is not None:
            row.name_fr = data.name_fr
        if data.image is not None:
            row.image = data.image
        row.updated_by = actor_id
        return self._repo.update(row)

    def delete(self, industry_id: str) -> bool:
        row = self._repo.get_by_id(industry_id)
        if row is None:
            return False
        self._repo.delete(row)
        return True
