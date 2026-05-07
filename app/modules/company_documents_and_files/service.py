"""Business logic for company documents and files."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.companies.service import CompanyService
from app.modules.company_documents_and_files.models import CompanyDocumentAndFile, DocumentMedia
from app.modules.company_documents_and_files.repository import CompanyDocumentAndFileRepository
from app.modules.company_documents_and_files.schemas import (
    CompanyDocumentAndFileCreate,
    CompanyDocumentAndFileUpdate,
    DocumentMediaCreate,
)


class CompanyDocumentAndFileService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyDocumentAndFileRepository(db)
        self._companies = CompanyService(db)

    def list_for_company_admin(self, company_id: str) -> list[CompanyDocumentAndFile] | None:
        if self._companies.get_company_by_id(company_id) is None:
            return None
        return self._repo.list_for_company(company_id, load_media=True)

    def get_for_company_admin(
        self,
        company_id: str,
        document_id: str,
    ) -> CompanyDocumentAndFile | None:
        if self._companies.get_company_by_id(company_id) is None:
            return None
        row = self._repo.get_by_id(document_id, load_media=True)
        if row is None or row.company_id != company_id:
            return None
        return row

    def list_for_owner(self, company_id: str, owner_id: str) -> list[CompanyDocumentAndFile] | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        return self._repo.list_for_company(company_id, load_media=True)

    def get_for_owner(
        self,
        company_id: str,
        document_id: str,
        owner_id: str,
    ) -> CompanyDocumentAndFile | None:
        if self._companies.get_company(company_id, owner_id) is None:
            return None
        row = self._repo.get_by_id(document_id, load_media=True)
        if row is None or row.company_id != company_id:
            return None
        return row

    def create(
        self,
        company_id: str,
        owner_id: str,
        data: CompanyDocumentAndFileCreate,
    ) -> CompanyDocumentAndFile:
        if self._companies.get_company(company_id, owner_id) is None:
            raise ValueError("Company not found or not owned by you.")
        row = CompanyDocumentAndFile(
            company_id=company_id,
            document_type=data.document_type.value,
            expiry_date=data.expiry_date,
            reminder_by_days=data.reminder_by_days,
        )
        try:
            created = self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not create document.") from e
        return self._repo.get_by_id(created.id, load_media=True) or created

    def update(
        self,
        company_id: str,
        document_id: str,
        owner_id: str,
        data: CompanyDocumentAndFileUpdate,
    ) -> CompanyDocumentAndFile | None:
        row = self.get_for_owner(company_id, document_id, owner_id)
        if row is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self._repo.get_by_id(row.id, load_media=True)
        if "document_type" in payload and payload["document_type"] is not None:
            row.document_type = payload["document_type"].value
            del payload["document_type"]
        for k, v in payload.items():
            setattr(row, k, v)
        try:
            self._repo.update(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not update document.") from e
        return self._repo.get_by_id(row.id, load_media=True)

    def delete(self, company_id: str, document_id: str, owner_id: str) -> bool:
        row = self._repo.get_by_id(document_id, load_media=False)
        if row is None or self._companies.get_company(company_id, owner_id) is None:
            return False
        if row.company_id != company_id:
            return False
        self._repo.delete(row)
        return True

    def add_media(
        self,
        company_id: str,
        document_id: str,
        owner_id: str,
        data: DocumentMediaCreate,
    ) -> DocumentMedia | None:
        row = self.get_for_owner(company_id, document_id, owner_id)
        if row is None:
            return None
        m = DocumentMedia(
            company_document_id=row.id,
            media_type=data.media_type.value,
            media_link=data.media_link,
        )
        try:
            return self._repo.create_media(m)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not add media.") from e

    def delete_media(
        self,
        company_id: str,
        document_id: str,
        media_id: str,
        owner_id: str,
    ) -> bool:
        if self.get_for_owner(company_id, document_id, owner_id) is None:
            return False
        m = self._repo.get_media(media_id)
        if m is None or m.company_document_id != document_id:
            return False
        self._repo.delete_media(m)
        return True
