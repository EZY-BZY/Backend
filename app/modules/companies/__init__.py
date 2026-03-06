"""
Companies (tenants) module.
Public API: CompanyService.
Each supplier company is a tenant; all tenant-scoped data is filtered by company_id.
"""

from app.modules.companies.service import CompanyService

__all__ = ["CompanyService"]
