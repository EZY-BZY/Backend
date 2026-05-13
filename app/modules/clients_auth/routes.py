"""Client auth routes."""

from datetime import datetime, timedelta, timezone
import logging
import secrets

from fastapi import APIRouter

from app.common.allenums import AccountStatus, ClientAccountType, ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.session import DbSession
from app.modules.beasy_employees.service import EmployeeService
from app.modules.clients_auth.schemas import (
    ChangePasswordWhileLoggedIn,
    ClientLoginRequest,
    ClientLoginResponse,
    CompanyEmployeeBasicRead,
    EmployeeBasicRead,
    ForgotPasswordChangePassword,
    ForgotPasswordRequestOTP,
    ForgotPasswordVerifyOTP,
    OwnerBasicRead,
)
from app.modules.companies.service import CompanyService
from app.modules.companies_owners.service import CompanyOwnerService
from app.modules.clients_auth.dependencies import CurrentClientRequired

router = APIRouter(prefix="/auth", tags=["Authentication (clients)"])
logger = logging.getLogger(__name__)

OTP_EXPIRE_MINUTES = 5
MAX_RESEND_ATTEMPTS = 5
MAX_VERIFY_ATTEMPTS = 5


def _generate_otp() -> str:
    settings = get_settings()
    if settings.environment != "production":
        return "000000"
    return f"{secrets.randbelow(1_000_000):06d}"


def _otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)


@router.post(
    "/login",
    response_model=ApiResponse[ClientLoginResponse],
    summary="Login (owner or employee)",
    description=(
        "Login endpoint for client apps.\n\n"
        "- `account_type=owner`: authenticate using `companies_owners`.\n"
        "- `account_type=employee`: authenticate using `beasy_employees` (by phone).\n"
        "- `account_type=company_employee`: authenticate using `company_employees` with an active phone in "
        "`company_employee_phones`.\n\n"
        "Notes:\n"
        "- Owners must have `is_verified_phone=true` and `account_status=active`.\n"
        "- Beasy employees must have `account_status=active` and must not be soft-deleted.\n"
        "- Company employees must be `is_active`, with a matching **active** row in "
        "`company_employee_phones` for the login phone.\n\n"
        "Returns access + refresh tokens, basic user data, and for **owners** a ``companies`` list "
        "(all rows where ``companies.owner_id`` is the owner; empty list if none). Other account types get "
        "``companies: []``."
    ),
)
def client_login(body: ClientLoginRequest, db: DbSession):
    settings = get_settings()

    if body.account_type == ClientAccountType.OWNER:
        try:
            owner = CompanyOwnerService(db).authenticate_owner(phone=body.phone, password=body.password)
        except ValueError as e:
            return json_error(ResponseEnum.ERROR.value, http_status=401, details=str(e))
        access = create_access_token(owner.id, extra_claims={"account_type": "owner"})
        refresh = create_refresh_token(owner.id)
        companies = CompanyService(db).companies_read_payload_for_owner(str(owner.id))
        payload = ClientLoginResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=OwnerBasicRead.model_validate(owner).model_dump(),
            companies=companies,
        ).model_dump()
        return json_success(payload, message=ResponseEnum.SUCCESS.value)

    if body.account_type == ClientAccountType.EMPLOYEE:
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
            companies=[],
        ).model_dump()
        return json_success(payload, message=ResponseEnum.SUCCESS.value)

    # COMPANY_EMPLOYEE (client company staff)
    from app.modules.company_employees.service import CompanyEmployeeService

    cemp = CompanyEmployeeService(db).authenticate_by_phone(body.phone, body.password)
    if not cemp:
        return json_error(ResponseEnum.ERROR.value, http_status=401, details="Invalid phone or password")
    access = create_access_token(
        cemp.id,
        company_id=cemp.company_id,
        extra_claims={
            "account_type": "company_employee",
            "company_employee_role": cemp.role,
        },
    )
    refresh = create_refresh_token(cemp.id)
    payload = ClientLoginResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=CompanyEmployeeBasicRead.model_validate(cemp).model_dump(),
        companies=[],
    ).model_dump()
    return json_success(payload, message=ResponseEnum.SUCCESS.value)


@router.post(
    "/forgot-password/request",
    response_model=ApiResponse[dict],
    summary="Request forgot password OTP",
    description=(
        "Step 1 of forgot-password flow.\n\n"
        "Security behavior:\n"
        "- Always returns success even if the phone does not exist.\n"
        "- Never returns the OTP.\n\n"
        "Behavior (if account exists):\n"
        "- Generates an OTP (dev/staging: fixed `000000`, production: random 6 digits)\n"
        "- Hashes OTP before saving\n"
        f"- Sets expiry to {OTP_EXPIRE_MINUTES} minutes\n"
        f"- Limits resend attempts to {MAX_RESEND_ATTEMPTS}\n\n"
        "Next step: call `/clients/auth/forgot-password/verify`."
    ),
)
def forgot_password_request(body: ForgotPasswordRequestOTP, db: DbSession):
    otp = _generate_otp()
    expires_at = _otp_expiry()

    if body.account_type == ClientAccountType.COMPANY_EMPLOYEE:
        return json_success({}, message=ResponseEnum.SUCCESS.value)

    # Do not reveal existence; just update if found.
    if body.account_type == ClientAccountType.OWNER:
        svc = CompanyOwnerService(db)
        row = svc.get_by_phone(body.phone)
        if row:
            if row.forgot_password_resend_attempts >= MAX_RESEND_ATTEMPTS:
                # still return generic success
                return json_success({}, message=ResponseEnum.SUCCESS.value)
            row.forgot_password_otp_hash = get_password_hash(otp)
            row.forgot_password_otp_expires_at = expires_at
            row.forgot_password_otp_verified_at = None
            row.forgot_password_verify_attempts = 0
            row.forgot_password_resend_attempts += 1
            row.forgot_password_last_sent_at = datetime.now(timezone.utc)
            svc._repo.update(row)  # internal commit/update
            logger.info("Forgot password OTP sent (dev=%s) to %s", get_settings().environment != "production", body.phone)
    elif body.account_type == ClientAccountType.EMPLOYEE:
        svc = EmployeeService(db)
        row = svc.get_by_phone(body.phone)
        if row:
            if row.forgot_password_resend_attempts >= MAX_RESEND_ATTEMPTS:
                return json_success({}, message=ResponseEnum.SUCCESS.value)
            row.forgot_password_otp_hash = get_password_hash(otp)
            row.forgot_password_otp_expires_at = expires_at
            row.forgot_password_otp_verified_at = None
            row.forgot_password_verify_attempts = 0
            row.forgot_password_resend_attempts += 1
            row.forgot_password_last_sent_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(row)
            logger.info("Forgot password OTP sent (dev=%s) to %s", get_settings().environment != "production", body.phone)

    return json_success({}, message=ResponseEnum.SUCCESS.value)


@router.post(
    "/forgot-password/verify",
    response_model=ApiResponse[dict],
    summary="Verify forgot password OTP",
    description=(
        "Step 2 of forgot-password flow.\n\n"
        "Validates the OTP by comparing it to the stored hashed OTP and checking expiry.\n"
        f"Limits verification attempts to {MAX_VERIFY_ATTEMPTS}.\n\n"
        "If valid, the OTP is marked as verified for password reset, but the password is NOT changed here.\n\n"
        "Next step: call `/clients/auth/forgot-password/change-password`."
    ),
)
def forgot_password_verify(body: ForgotPasswordVerifyOTP, db: DbSession):
    now = datetime.now(timezone.utc)

    if body.account_type == ClientAccountType.COMPANY_EMPLOYEE:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid OTP")

    if body.account_type == ClientAccountType.OWNER:
        svc = CompanyOwnerService(db)
        row = svc.get_by_phone(body.phone)
        if not row:
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid OTP")
        if not row.forgot_password_otp_hash or not row.forgot_password_otp_expires_at:
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="OTP not requested")
        if row.forgot_password_otp_verified_at:
            return json_success({}, message=ResponseEnum.SUCCESS.value)
        if row.forgot_password_verify_attempts >= MAX_VERIFY_ATTEMPTS:
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="Too many attempts")
        if row.forgot_password_otp_expires_at < now:
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="OTP expired")
        if not verify_password(body.otp, row.forgot_password_otp_hash):
            row.forgot_password_verify_attempts += 1
            svc._repo.update(row)
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid OTP")
        row.forgot_password_otp_verified_at = now
        svc._repo.update(row)
        return json_success({}, message=ResponseEnum.SUCCESS.value)

    # EMPLOYEE
    row = EmployeeService(db).get_by_phone(body.phone)
    if not row:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid OTP")
    if not row.forgot_password_otp_hash or not row.forgot_password_otp_expires_at:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="OTP not requested")
    if row.forgot_password_otp_verified_at:
        return json_success({}, message=ResponseEnum.SUCCESS.value)
    if row.forgot_password_verify_attempts >= MAX_VERIFY_ATTEMPTS:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Too many attempts")
    if row.forgot_password_otp_expires_at < now:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="OTP expired")
    if not verify_password(body.otp, row.forgot_password_otp_hash):
        row.forgot_password_verify_attempts += 1
        db.commit()
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid OTP")
    row.forgot_password_otp_verified_at = now
    db.commit()
    return json_success({}, message=ResponseEnum.SUCCESS.value)


@router.post(
    "/forgot-password/change-password",
    response_model=ApiResponse[dict],
    summary="Change password after OTP verification",
    description=(
        "Step 3 (final) of forgot-password flow.\n\n"
        "Rules:\n"
        "- Requires OTP to be verified first (from `/forgot-password/verify`).\n"
        "- `new_password` must match `confirm_password`.\n"
        "- Hashes the new password before saving.\n"
        "- Clears OTP hash/expiry/verified flag after success.\n\n"
        "Does not return any password/OTP fields."
    ),
)
def forgot_password_change_password(body: ForgotPasswordChangePassword, db: DbSession):
    if body.new_password != body.confirm_password:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Passwords do not match")

    if body.account_type == ClientAccountType.COMPANY_EMPLOYEE:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid request")

    if body.account_type == ClientAccountType.OWNER:
        svc = CompanyOwnerService(db)
        row = svc.get_by_phone(body.phone)
        if not row:
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid request")
        if not row.forgot_password_otp_verified_at:
            return json_error(ResponseEnum.FAIL.value, http_status=400, details="OTP not verified")
        row.password_hash = get_password_hash(body.new_password)
        row.forgot_password_otp_hash = None
        row.forgot_password_otp_expires_at = None
        row.forgot_password_otp_verified_at = None
        row.forgot_password_verify_attempts = 0
        row.forgot_password_resend_attempts = 0
        svc._repo.update(row)
        return json_success({}, message=ResponseEnum.SUCCESS.value)

    if body.account_type != ClientAccountType.EMPLOYEE:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid request")

    row = EmployeeService(db).get_by_phone(body.phone)
    if not row:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Invalid request")
    if not row.forgot_password_otp_verified_at:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="OTP not verified")
    row.password_hash = get_password_hash(body.new_password)
    row.forgot_password_otp_hash = None
    row.forgot_password_otp_expires_at = None
    row.forgot_password_otp_verified_at = None
    row.forgot_password_verify_attempts = 0
    row.forgot_password_resend_attempts = 0
    db.commit()
    return json_success({}, message=ResponseEnum.SUCCESS.value)


@router.patch(
    "/change-password",
    response_model=ApiResponse[dict],
    summary="Change password (logged in)",
    description=(
        "Change password for an authenticated user.\n\n"
        "Authentication:\n"
        "- Requires `Authorization: Bearer <access_token>`.\n"
        "- Detects `owner|employee|company_employee` from the token claim `account_type`.\n\n"
        "Rules:\n"
        "- Validates `old_password`.\n"
        "- `new_password` must match `confirm_password`.\n"
        "- `new_password` must be different from `old_password`.\n\n"
        "Does not return any password fields."
    ),
)
def change_password_logged_in(body: ChangePasswordWhileLoggedIn, db: DbSession, current: CurrentClientRequired):
    if body.new_password != body.confirm_password:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="Passwords do not match")
    if body.new_password == body.old_password:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="New password must be different")

    if current["account_type"] == "owner":
        svc = CompanyOwnerService(db)
        row = svc.get_by_id(current["user_id"])
        if not row or not verify_password(body.old_password, row.password_hash):
            return json_error(ResponseEnum.ERROR.value, http_status=401, details="Invalid old password")
        row.password_hash = get_password_hash(body.new_password)
        svc._repo.update(row)
        return json_success({}, message=ResponseEnum.SUCCESS.value)

    if current["account_type"] == "employee":
        row = EmployeeService(db).get_by_id(current["user_id"], include_deleted=False)
        if not row or not verify_password(body.old_password, row.password_hash):
            return json_error(ResponseEnum.ERROR.value, http_status=401, details="Invalid old password")
        row.password_hash = get_password_hash(body.new_password)
        db.commit()
        return json_success({}, message=ResponseEnum.SUCCESS.value)

    from app.modules.company_employees.repository import CompanyEmployeeRepository

    row = CompanyEmployeeRepository(db).get_employee(current["user_id"], load_children=False)
    if not row or not row.is_active or not verify_password(body.old_password, row.password_hash):
        return json_error(ResponseEnum.ERROR.value, http_status=401, details="Invalid old password")
    row.password_hash = get_password_hash(body.new_password)
    db.commit()
    return json_success({}, message=ResponseEnum.SUCCESS.value)

