"""Pydantic schemas for terms APIs."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.terms.enums import HistoryAction, TermType


class TermCreate(BaseModel):
    name_en: str = Field(..., max_length=512)
    name_ar: str = Field(..., max_length=512)
    name_fr: str = Field(..., max_length=512)
    description_en: str
    description_ar: str
    description_fr: str
    type: TermType
    order: int | None = Field(
        None,
        ge=1,
        description="Display order within this type. Omit to append (max existing + 1).",
    )


class TermUpdate(BaseModel):
    name_en: str | None = Field(None, max_length=512)
    name_ar: str | None = Field(None, max_length=512)
    name_fr: str | None = Field(None, max_length=512)
    description_en: str | None = None
    description_ar: str | None = None
    description_fr: str | None = None
    order: int | None = Field(None, ge=1)


class TermPublicRead(BaseModel):
    """Public-safe payload: names, descriptions, type, and display order only."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name_en: str
    name_ar: str
    name_fr: str
    description_en: str
    description_ar: str
    description_fr: str
    type: TermType = Field(validation_alias="term_type")
    order: int = Field(validation_alias="sort_order")


class TermRead(BaseModel):
    """Full term row for Beasy admin / CUD responses."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name_en: str
    name_ar: str
    name_fr: str
    description_en: str
    description_ar: str
    description_fr: str
    type: TermType = Field(validation_alias="term_type")
    order: int = Field(validation_alias="sort_order")
    created_by: str | None
    created_at: datetime
    updated_by: str | None
    updated_at: datetime
    deleted_at: datetime | None = None


class TermSnapshotItem(BaseModel):
    """One term row inside a version snapshot (audit / history only)."""

    name_en: str
    name_ar: str
    name_fr: str
    description_en: str
    description_ar: str
    description_fr: str
    type: TermType
    order: int
    is_changed: bool


class TermHistoryVersionRead(BaseModel):
    """Single change event: full type snapshot at that moment."""

    version_date: datetime = Field(validation_alias="version_at")
    action_type: HistoryAction = Field(validation_alias="action")
    performed_by: str | None
    changed_term_id: str
    terms_snapshot: list[TermSnapshotItem]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TermHistoryDayGroupRead(BaseModel):
    """History versions grouped by calendar day (UTC), newest day first within the page."""

    day: date
    versions: list[TermHistoryVersionRead]
