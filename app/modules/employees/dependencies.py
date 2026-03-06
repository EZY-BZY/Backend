"""
Organization auth and permission dependencies.
- get_current_employee: load Employee from JWT (sub = employee_id).
- require_permission(permission_name): reusable dependency that checks permission from DB.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import DbSession
from app.modules.employees.models import Employee
from app.modules.employees.service import EmployeeService

# Use same Bearer scheme as main auth; JWT sub must be employee_id for org routes
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
) -> Employee | None:
    """
    Load current employee from JWT (sub = employee_id).
    Returns None if no/invalid token. Use get_current_employee_required when auth is required.
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
    current: Annotated[Employee | None, Depends(get_current_employee)],
) -> Employee:
    """Require authenticated employee; raise 401 if not."""
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current


def get_current_active_employee(
    current: Annotated[Employee, Depends(get_current_employee_required)],
) -> Employee:
    """Require active account (not inactive/suspended)."""
    if current.account_status not in ("active",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )
    return current


def require_permission(permission_name: str):
    """
    Reusable dependency: require the given permission for the current employee.
    Reads permissions from database (employee_permissions table).
    Usage: Depends(require_permission("manage_terms")), Depends(require_permission("view_members")), etc.
    """

    def _require(
        current_employee: Annotated[Employee, Depends(get_current_active_employee)],
        db: DbSession,
    ) -> Employee:
        svc = EmployeeService(db)
        if not svc.employee_has_permission(current_employee.id, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_name}",
            )
        return current_employee

    return _require


# Type aliases for route injection
CurrentEmployee = Annotated[Employee | None, Depends(get_current_employee)]
CurrentEmployeeRequired = Annotated[Employee, Depends(get_current_active_employee)]
