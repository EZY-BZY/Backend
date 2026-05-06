"""Client auth routes."""

from fastapi import APIRouter

from app.common.allenums import AccountStatus, ClientAccountType, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.db.session import DbSession
from app.modules.beasy_employees.service import EmployeeService
from app.modules.clients_auth.schemas import (
    ClientLoginRequest,
    ClientLoginResponse,
    EmployeeBasicRead,
    OwnerBasicRead,
)
from app.modules.companies_owners.service import CompanyOwnerService

router = APIRouter(prefix="/auth", tags=["Authentication (clients)"])


@router.post("/login", response_model=ApiResponse[ClientLoginResponse])
def client_login(body: ClientLoginRequest, db: DbSession):
    settings = get_settings()

    if body.account_type == ClientAccountType.OWNER:
        try:
            owner = CompanyOwnerService(db).authenticate_owner(phone=body.phone, password=body.password)
        except ValueError as e:
            return json_error(ResponseEnum.ERROR.value, http_status=401, details=str(e))
        access = create_access_token(owner.id, extra_claims={"account_type": "owner"})
        refresh = create_refresh_token(owner.id)
        payload = ClientLoginResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=OwnerBasicRead.model_validate(owner).model_dump(),
        ).model_dump()
        return json_success(payload, message=ResponseEnum.SUCCESS.value)

    # EMPLOYEE
    employee = EmployeeService(db).get_by_phone(body.phone)
    if not employee or not verify_password(body.password, employee.password_hash):
        return json_error(ResponseEnum.ERROR.value, http_status=401, details="Invalid phone or password")
    if employee.deleted_at:
        return json_error(ResponseEnum.ERROR.value, http_status=403, details="Account is deactivated")
    if employee.account_status != AccountStatus.ACTIVE.value:
        return json_error(ResponseEnum.ERROR.value, http_status=403, details="Account is inactive or suspended")

    access = create_access_token(employee.id, extra_claims={"account_type": "employee"})
    refresh = create_refresh_token(employee.id)
    payload = ClientLoginResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=EmployeeBasicRead.model_validate(employee).model_dump(),
    ).model_dump()
    return json_success(payload, message=ResponseEnum.SUCCESS.value)

