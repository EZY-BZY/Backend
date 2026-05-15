"""Access control for company-scoped branch APIs (owners vs employees)."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentClient
from app.modules.companies.service import CompanyService


def ensure_client_company_access(db: DbSession, current: CurrentClient, company_id: str) -> None:
    """
    Owners: ``company_id`` must be one of their companies.
    Employees: JWT must include ``company_id`` matching the path (set when issuing employee tokens).
    """
    cid = str(company_id)
    if current["account_type"] == "owner":
        if CompanyService(db).get_company(cid, current["user_id"]) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        return
    token_company = current.get("company_id")
    if not token_company or str(token_company) != cid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed for this company (employee token needs matching company_id).",
        )


def is_company_insider(db: DbSession, current: CurrentClient | None, company_id: str) -> bool:
    """
    True when the caller is the company owner or a company employee for this company.
    All other callers (anonymous, Beasy staff, other owners) are public viewers.
    """
    if current is None:
        return False
    cid = str(company_id)
    if current["account_type"] == "owner":
        return CompanyService(db).get_company(cid, current["user_id"]) is not None
    if current["account_type"] == "company_employee":
        return str(current.get("company_id") or "") == cid
    return False
