"""Data access for fixed_assets and assets_media."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.fixed_assets.models import AssetMedia, FixedAsset


class FixedAssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, row_id: str, *, load_media: bool = False) -> FixedAsset | None:
        if not load_media:
            return self.db.get(FixedAsset, row_id)
        stmt = (
            select(FixedAsset)
            .where(FixedAsset.id == row_id)
            .options(selectinload(FixedAsset.media))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_company(self, company_id: str, *, load_media: bool = False) -> list[FixedAsset]:
        stmt = select(FixedAsset).where(FixedAsset.company_id == company_id)
        if load_media:
            stmt = stmt.options(selectinload(FixedAsset.media))
        stmt = stmt.order_by(FixedAsset.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, row: FixedAsset) -> FixedAsset:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: FixedAsset) -> FixedAsset:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: FixedAsset) -> None:
        self.db.delete(row)
        self.db.commit()

    def get_media(self, media_id: str) -> AssetMedia | None:
        return self.db.get(AssetMedia, media_id)

    def create_media(self, row: AssetMedia) -> AssetMedia:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_media(self, row: AssetMedia) -> None:
        self.db.delete(row)
        self.db.commit()
