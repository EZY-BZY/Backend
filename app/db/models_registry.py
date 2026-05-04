"""
Import all ORM models so Alembic and SQLAlchemy can discover them.
Do not use for business logic - this is only for metadata/schema.
"""
from app.db.base import Base

# Active module after reset.
from app.modules.beasy_employees.models import BEasyEmployee  # noqa: F401
from app.modules.industries.models import Industry  # noqa: F401
from app.modules.terms.models import Term, TermHistory  # noqa: F401

__all__ = ["Base"]
