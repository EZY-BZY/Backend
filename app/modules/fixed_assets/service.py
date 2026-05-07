"""Business logic for company fixed assets."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.companies.service import CompanyService
from app.modules.fixed_assets.models import AssetMedia, FixedAsset
from app.modules.fixed_assets.repository import FixedAssetRepository
from app.modules.fixed_assets.schemas import (
    FixedAssetCreate,
    FixedAssetMediaCreate,
    FixedAssetUpdate,
)


class FixedAssetService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = FixedAssetRepository(db)
        self._companies = CompanyService(db)

    def list_for_company_admin(self, company_id: str) -> list[FixedAsset] | None:
        if self._companies.get_company_by_id(company_id) is None:
            return None
        return self._repo.list_for_company(company_id, load_media=True)

    def get_for_company_admin(
        self,
        company_id: str,
        asset_id: str,
    ) -> FixedAsset | None:
        if self._companies.get_company_by_id(company_id) is None:
            return None
        row = self._repo.get_by_id(asset_id, load_media=True)
        if row is None or row.company_id != company_id:
            return None
        return row

    def list_for_owner(self, company_id: str, owner_id: str) -> list[FixedAsset] | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        return self._repo.list_for_company(company_id, load_media=True)

    def get_for_owner(
        self,
        company_id: str,
        asset_id: str,
        owner_id: str,
    ) -> FixedAsset | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        row = self._repo.get_by_id(asset_id, load_media=True)
        if row is None or row.company_id != company_id:
            return None
        return row

    def create(
        self,
        company_id: str,
        owner_id: str,
        data: FixedAssetCreate,
    ) -> FixedAsset:
        if self._companies.get_company(company_id, owner_id) is None:
            raise ValueError("Company not found or not owned by you.")
        row = FixedAsset(
            company_id=company_id,
            asset_name=data.asset_name,
            asset_type=data.asset_type.value,
            details=data.details,
            location_description=data.location_description,
        )
        try:
            created = self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create fixed asset.") from e
        return self._repo.get_by_id(created.id, load_media=True) or created

    def create_with_media_urls(
        self,
        company_id: str,
        owner_id: str,
        data: FixedAssetCreate,
        media_pairs: list[tuple[str, str]],
    ) -> FixedAsset:
        """Create asset then attach media rows. Rolls back the asset if any media insert fails."""
        row = self.create(company_id, owner_id, data)
        try:
            for media_type, url in media_pairs:
                self.add_media(
                    company_id,
                    row.id,
                    owner_id,
                    FixedAssetMediaCreate(media_type=media_type, media_link=url),
                )
        except ValueError:
            self.delete(company_id, row.id, owner_id)
            raise
        reloaded = self._repo.get_by_id(row.id, load_media=True)
        return reloaded or row

    def update(
        self,
        company_id: str,
        asset_id: str,
        owner_id: str,
        data: FixedAssetUpdate,
    ) -> FixedAsset | None:
        row = self.get_for_owner(company_id, asset_id, owner_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self._repo.get_by_id(row.id, load_media=True)
        if "asset_type" in payload and payload["asset_type"] is not None:
            row.asset_type = payload["asset_type"].value
            del payload["asset_type"]
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            self._repo.update(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update fixed asset.") from e
        return self._repo.get_by_id(row.id, load_media=True)

    def delete(self, company_id: str, asset_id: str, owner_id: str) -> bool:
        row = self._repo.get_by_id(asset_id, load_media=False)
        if row is None or self._companies.get_company(company_id, owner_id) is None:
            return False
        if row.company_id != company_id:
            return False
        self._repo.delete(row)
        return True

    def add_media(
        self,
        company_id: str,
        asset_id: str,
        owner_id: str,
        data: FixedAssetMediaCreate,
    ) -> AssetMedia | None:
        row = self.get_for_owner(company_id, asset_id, owner_id)
        if row is None:
            return None
        m = AssetMedia(
            asset_id=row.id,
            media_type=data.media_type,
            media_link=data.media_link,
        )
        try:
            return self._repo.create_media(m)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not add media.") from e

    def add_media_from_url(
        self,
        company_id: str,
        asset_id: str,
        owner_id: str,
        *,
        media_type: str,
        media_link: str,
    ) -> AssetMedia | None:
        return self.add_media(
            company_id,
            asset_id,
            owner_id,
            FixedAssetMediaCreate(media_type=media_type, media_link=media_link),
        )

    def delete_media(
        self,
        company_id: str,
        asset_id: str,
        media_id: str,
        owner_id: str,
    ) -> bool:
        if self.get_for_owner(company_id, asset_id, owner_id) is None:
            return False
        m = self._repo.get_media(media_id)
        if m is None or m.asset_id != asset_id:
            return False
        self._repo.delete_media(m)
        return True
