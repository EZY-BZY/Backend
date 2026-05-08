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
