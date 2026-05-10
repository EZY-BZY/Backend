"""Access control: only company owners or company employees with role ``admin``."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.common.allenums import CompanyEmployeeRole
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentClient, get_current_client
from app.modules.company_employees.repository import CompanyEmployeeRepository
from app.modules.companies.service import CompanyService


def ensure_employer_manage_access(db: DbSession, current: CurrentClient, company_id: str) -> None:
    """
    Owners: must own the company.
    Company employees: JWT must be a company employee admin for this company (re-validated in DB).
    """
    cid = str(company_id)
    if current["account_type"] == "owner":
        if CompanyService(db).get_company(cid, current["user_id"]) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return

    if current["account_type"] != "company_employee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if str(current.get("company_id") or "") != cid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this company")

    emp = CompanyEmployeeRepository(db).get_employee(str(current["user_id"]), load_children=False)
    if (
        emp is None
        or not emp.is_active
        or emp.company_id != cid
        or emp.role != CompanyEmployeeRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company admins can manage employees.",
        )


def get_current_employer(
    current: Annotated[CurrentClient, Depends(get_current_client)],
) -> CurrentClient:
    """Fast path: owners always; company employees must carry admin role in token."""
    if current["account_type"] == "owner":
        return current
    if current["account_type"] == "company_employee":
        if current.get("company_employee_role") != CompanyEmployeeRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only company admins can manage employees.",
            )
        return current
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


CurrentEmployerRequired = Annotated[CurrentClient, Depends(get_current_employer)]
