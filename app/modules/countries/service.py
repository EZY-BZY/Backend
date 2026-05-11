"""Country CRUD with duplicate prevention and regex validation."""

import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.countries.models import Country
from app.modules.countries.repository import CountryRepository
from app.modules.countries.schemas import CountryCreate, CountryUpdate


class CountryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CountryRepository(db)

    def get_by_id(self, country_id: str) -> Country | None:
        return self._repo.get_by_id(country_id)

    def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Country], int]:
        skip = (page - 1) * page_size
        return self._repo.list_paginated(skip=skip, limit=page_size)

    @staticmethod
    def _ensure_regex_compiles(phone_regex: str) -> None:
        try:
            re.compile(phone_regex)
        except re.error as e:
            raise ValueError(f"Invalid phone_regex: {e}") from e

    def create(self, data: CountryCreate, actor_id: str) -> Country:
        self._ensure_regex_compiles(data.phone_regex)

        if self._repo.get_by_phone_code(data.phone_code):
            raise ValueError("A country with this phone code already exists.")
        if self._repo.get_by_name_en(data.name_en):
            raise ValueError("A country with this English name already exists.")

        row = Country(
            phone_code=data.phone_code,
            name_en=data.name_en,
            name_ar=data.name_ar,
            name_fr=data.name_fr,
            phone_regex=data.phone_regex,
            currency_shortcut_en=data.currency_shortcut_en,
            currency_shortcut_ar=data.currency_shortcut_ar,
            currency_shortcut_fr=data.currency_shortcut_fr,
            currency_name_en=data.currency_name_en,
            currency_name_ar=data.currency_name_ar,
            currency_name_fr=data.currency_name_fr,
            flag_emoji=data.flag_emoji,
            created_by=actor_id,
            updated_by=actor_id,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError(f"Could not create country (duplicate or constraint violation). {e}") from e

    def update(self, country_id: str, data: CountryUpdate, actor_id: str) -> Country | None:
        row = self._repo.get_by_id(country_id)
        if row is None:
            return None

        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return row

        if data.phone_regex is not None:
            self._ensure_regex_compiles(data.phone_regex)

        if data.phone_code is not None and data.phone_code != row.phone_code:
            if self._repo.get_by_phone_code(data.phone_code):
                raise ValueError("A country with this phone code already exists.")
            row.phone_code = data.phone_code

        if data.name_en is not None and data.name_en != row.name_en:
            if self._repo.get_by_name_en(data.name_en):
                raise ValueError("A country with this English name already exists.")
            row.name_en = data.name_en

        if data.name_ar is not None:
            row.name_ar = data.name_ar
        if data.name_fr is not None:
            row.name_fr = data.name_fr
        if data.phone_regex is not None:
            row.phone_regex = data.phone_regex
        if data.currency_shortcut_en is not None:
            row.currency_shortcut_en = data.currency_shortcut_en
        if data.currency_shortcut_ar is not None:
            row.currency_shortcut_ar = data.currency_shortcut_ar
        if data.currency_shortcut_fr is not None:
            row.currency_shortcut_fr = data.currency_shortcut_fr
        if data.currency_name_en is not None:
            row.currency_name_en = data.currency_name_en
        if data.currency_name_ar is not None:
            row.currency_name_ar = data.currency_name_ar
        if data.currency_name_fr is not None:
            row.currency_name_fr = data.currency_name_fr
        if data.flag_emoji is not None:
            row.flag_emoji = data.flag_emoji

        row.updated_by = actor_id

        try:
            return self._repo.update(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update country (duplicate or constraint violation).") from e

    def delete(self, country_id: str) -> bool:
        row = self._repo.get_by_id(country_id)
        if row is None:
            return False
        self._repo.delete(row)
        return True

