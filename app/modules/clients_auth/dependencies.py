"""Client auth dependencies (owner/employee from JWT)."""

from __future__ import annotations

from typing import Annotated, Literal, NotRequired, TypedDict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.session import DbSession
from app.modules.beasy_employees.service import EmployeeService
from app.modules.companies_owners.service import CompanyOwnerService

http_bearer = HTTPBearer(auto_error=False)


AccountTypeLiteral = Literal["owner", "employee", "company_employee"]


class CurrentClient(TypedDict):
    account_type: AccountTypeLiteral
    user_id: str
    company_id: NotRequired[str | None]
    company_employee_role: NotRequired[str | None]


def get_current_client(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> CurrentClient:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials, expected_type="access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    sub = payload.get("sub")
    account_type = payload.get("account_type")
    if not sub or account_type not in ("owner", "employee", "company_employee"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if account_type == "owner":
        row = CompanyOwnerService(db).get_by_id(str(sub))
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")
        return {
            "account_type": "owner",
            "user_id": str(sub),
            "company_id": payload.get("company_id"),
        }

    if account_type == "employee":
        row = EmployeeService(db).get_by_id(str(sub), include_deleted=False)
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")
        return {
            "account_type": "employee",
            "user_id": str(sub),
            "company_id": payload.get("company_id"),
        }

    # company_employee — subject is ``company_employees.id`` (avoid import cycle with lazy load).
    from app.modules.company_employees.repository import CompanyEmployeeRepository

    cerow = CompanyEmployeeRepository(db).get_employee(str(sub), load_children=False)
    if not cerow or not cerow.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")
    return {
        "account_type": "company_employee",
        "user_id": str(sub),
        "company_id": str(cerow.company_id),
        "company_employee_role": cerow.role,
    }


CurrentClientRequired = Annotated[CurrentClient, Depends(get_current_client)]


def get_optional_current_client(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> CurrentClient | None:
    """Return the authenticated client, or ``None`` when no/invalid token (no 401)."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials, expected_type="access")
    if not payload:
        return None
    sub = payload.get("sub")
    account_type = payload.get("account_type")
    if not sub or account_type not in ("owner", "employee", "company_employee"):
        return None
    try:
        return get_current_client(db, credentials)
    except HTTPException:
        return None


OptionalCurrentClient = Annotated[CurrentClient | None, Depends(get_optional_current_client)]


def get_current_owner_required(
    current: Annotated[CurrentClient, Depends(get_current_client)],
) -> CurrentClient:
    if current["account_type"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners can perform this action",
        )
    return current


CurrentOwnerRequired = Annotated[CurrentClient, Depends(get_current_owner_required)]
