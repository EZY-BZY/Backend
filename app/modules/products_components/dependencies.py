"""Audit actor helpers and company access checks for products & components."""

from __future__ import annotations

from app.common.allenums import CompanyAuditActorType
from app.modules.clients_auth.dependencies import CurrentClient
from app.modules.company_branches.dependencies import is_company_insider

__all__ = ["audit_from_current", "is_company_insider"]


def audit_from_current(current: CurrentClient) -> tuple[str, str]:
    """Map JWT to ``created_by_type`` / ``created_by_id`` (company_owner | employee)."""
    if current["account_type"] == "owner":
        return (CompanyAuditActorType.COMPANY_OWNER.value, current["user_id"])
    return (CompanyAuditActorType.EMPLOYEE.value, current["user_id"])
