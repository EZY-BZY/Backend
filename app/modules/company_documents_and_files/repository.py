"""Data access for company_documents_and_files and documents_media."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.company_documents_and_files.models import CompanyDocumentAndFile, DocumentMedia


class CompanyDocumentAndFileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, row_id: str, *, load_media: bool = False) -> CompanyDocumentAndFile | None:
        if not load_media:
            return self.db.get(CompanyDocumentAndFile, row_id)
        stmt = (
            select(CompanyDocumentAndFile)
            .where(CompanyDocumentAndFile.id == row_id)
            .options(selectinload(CompanyDocumentAndFile.media))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_company(
        self, company_id: str, *, load_media: bool = False
    ) -> list[CompanyDocumentAndFile]:
        stmt = select(CompanyDocumentAndFile).where(CompanyDocumentAndFile.company_id == company_id)
        if load_media:
            stmt = stmt.options(selectinload(CompanyDocumentAndFile.media))
        stmt = stmt.order_by(CompanyDocumentAndFile.expiry_date.asc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, row: CompanyDocumentAndFile) -> CompanyDocumentAndFile:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: CompanyDocumentAndFile) -> CompanyDocumentAndFile:
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: CompanyDocumentAndFile) -> None:
        self.db.delete(row)
        self.db.commit()

    def get_media(self, media_id: str) -> DocumentMedia | None:
        return self.db.get(DocumentMedia, media_id)

    def create_media(self, row: DocumentMedia) -> DocumentMedia:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_media(self, row: DocumentMedia) -> None:
        self.db.delete(row)
        self.db.commit()
