"""Company repository - data access. Internal to companies module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.companies.models import Company


class CompanyRepository:
    """Data access for companies."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, company_id: UUID | str) -> Company | None:
        """Get company by primary key."""
        return self.db.get(Company, str(company_id))

    def get_by_slug(self, slug: str) -> Company | None:
        """Get company by slug."""
        stmt = select(Company).where(Company.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, company: Company) -> Company:
        """Persist a new company."""
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def update(self, company: Company) -> Company:
        """Commit changes to company."""
        self.db.commit()
        self.db.refresh(company)
        return company

    def list_active(self, *, skip: int = 0, limit: int = 100) -> list[Company]:
        """List active companies with pagination."""
        stmt = select(Company).where(Company.is_active).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
