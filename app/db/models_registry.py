"""
Import all ORM models so Alembic and SQLAlchemy can discover them.
Do not use for business logic - this is only for metadata/schema.
"""
from app.db.base import Base

# Active module after reset.
from app.modules.app_permissions.models import AppPermission, AppPermissionHistory  # noqa: F401
from app.modules.banks_and_wallets.models import BankAndWallet  # noqa: F401
from app.modules.beasy_employees.models import BEasyEmployee  # noqa: F401
from app.modules.companies.models import Company, CompanyIndustry  # noqa: F401
from app.modules.company_contact_info.models import CompanyContactInfo  # noqa: F401
from app.modules.company_documents_and_files.models import CompanyDocumentAndFile, DocumentMedia  # noqa: F401
from app.modules.company_financials_accounts.models import CompanyFinancialsAccount  # noqa: F401
from app.modules.fixed_assets.models import AssetMedia, FixedAsset  # noqa: F401
from app.modules.countries.models import Country  # noqa: F401
from app.modules.industries.models import Industry  # noqa: F401
from app.modules.terms.models import Term, TermHistory  # noqa: F401

__all__ = ["Base"]
