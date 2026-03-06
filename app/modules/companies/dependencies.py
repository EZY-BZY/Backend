"""Companies module dependencies (inject repository/service)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.service import CompanyService


def get_company_repository(db: DbSession) -> CompanyRepository:
    """Provide company repository."""
    return CompanyRepository(db)


def get_company_service(db: DbSession) -> CompanyService:
    """Provide company service - use this in routes."""
    return CompanyService(db)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
