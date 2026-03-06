"""Terms module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.terms.service import TermService


def get_term_service(db: DbSession) -> TermService:
    return TermService(db)


TermServiceDep = Annotated[TermService, Depends(get_term_service)]
