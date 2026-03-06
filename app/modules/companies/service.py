"""Company service - business logic. Public API of companies module."""

from uuid import UUID

from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.schemas import CompanyCreate, CompanyUpdate
from sqlalchemy.orm import Session


class CompanyService:
    """Public service for company operations."""

    def __init__(self, db: Session) -> None:
        self._repo = CompanyRepository(db)

    def get_by_id(self, company_id: UUID | str) -> Company | None:
        """Get company by id."""
        return self._repo.get_by_id(company_id)

    def get_by_slug(self, slug: str) -> Company | None:
        """Get company by slug."""
        return self._repo.get_by_slug(slug)

    def create(self, data: CompanyCreate) -> Company:
        """Create a new company (e.g. during registration)."""
        company = Company(
            name=data.name,
            slug=data.slug,
            description=data.description,
            is_active=data.is_active,
        )
        return self._repo.create(company)

    def update(self, company_id: UUID | str, data: CompanyUpdate) -> Company | None:
        """Update company; returns None if not found."""
        company = self._repo.get_by_id(company_id)
        if not company:
            return None
        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(company, k, v)
        return self._repo.update(company)
