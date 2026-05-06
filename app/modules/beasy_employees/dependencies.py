"""
Organization auth dependencies.
- get_current_employee: load BEasyEmployee from JWT (sub = employee_id).
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import DbSession
from app.common.allenums import AccountStatus
from app.modules.beasy_employees.models import BEasyEmployee
from app.modules.beasy_employees.service import EmployeeService

http_bearer = HTTPBearer(auto_error=False)


def _get_token_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict | None:
    if not credentials:
        return None
    return decode_token(credentials.credentials)


def get_current_employee(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> BEasyEmployee | None:
    """
    Load current employee from JWT (sub = employee_id).
    Returns None if no/invalid token.
    """
    payload = _get_token_payload(credentials)
    if not payload or payload.get("type") != "access":
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    svc = EmployeeService(db)
    return svc.get_by_id(sub, include_deleted=False)


def get_current_employee_required(
    current: Annotated[BEasyEmployee | None, Depends(get_current_employee)],
) -> BEasyEmployee:
    """Require authenticated employee; raise 401 if not."""
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current


def get_current_active_employee(
    current: Annotated[BEasyEmployee, Depends(get_current_employee_required)],
) -> BEasyEmployee:
    """Require active account (not inactive/suspended)."""
    if current.account_status != AccountStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )
    return current


CurrentEmployee = Annotated[BEasyEmployee | None, Depends(get_current_employee)]
CurrentEmployeeRequired = Annotated[BEasyEmployee, Depends(get_current_active_employee)]
