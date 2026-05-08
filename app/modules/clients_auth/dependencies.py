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


AccountTypeLiteral = Literal["owner", "employee"]


class CurrentClient(TypedDict):
    account_type: AccountTypeLiteral
    user_id: str
    company_id: NotRequired[str | None]


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
    if not sub or account_type not in ("owner", "employee"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Ensure subject exists.
    if account_type == "owner":
        row = CompanyOwnerService(db).get_by_id(str(sub))
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")
    else:
        row = EmployeeService(db).get_by_id(str(sub), include_deleted=False)
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")

    return {
        "account_type": account_type,
        "user_id": str(sub),
        "company_id": payload.get("company_id"),
    }


CurrentClientRequired = Annotated[CurrentClient, Depends(get_current_client)]

# NOTE: This Todo will be implemented later but ignore for now.
# TODO: NOT ONLY company owner but also employees can perform this action, when we create the employees module.
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

