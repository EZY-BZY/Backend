"""Client-facing routes for company owner registration/verification."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.clients_auth.dependencies import CurrentOwnerRequired
from app.modules.companies_owners.schemas import (
    CompanyOwnerPublicRead,
    OwnerCheckPhoneResponse,
    OwnerRegisterRequest,
    OwnerResendOtpWithPasswordRequest,
    OwnerVerifyPhoneRequest,
)
from app.modules.companies_owners.service import CompanyOwnerService

router = APIRouter(prefix="/owners", tags=["Owners (clients)"])


def _svc(db: DbSession) -> CompanyOwnerService:
    return CompanyOwnerService(db)


@router.get(
    "/check-phone",
    response_model=ApiResponse[OwnerCheckPhoneResponse],
    summary="Check phone registration and verification status",
    description=(
        "Looks up the given phone in `companies_owners` (after trimming whitespace) and returns the "
        "current registration and verification state.\n\n"
        "**Response fields**\n"
        "- `registered`: `true` if an owner row exists for this phone (unique in the system).\n"
        "- `is_verified_phone`: `true` only when that owner has completed phone verification; "
        "`false` if there is no row yet or the owner exists but is still unverified.\n\n"
        "**How the app usually uses this**\n"
        "- `registered=false` → phone is free: continue with `POST /owners/register`.\n"
        "- `registered=true` and `is_verified_phone=false` → owner exists but phone not verified yet: "
        "call `POST /owners/resend-phone-otp` (Bearer owner token) or "
        "`POST /owners/resend-phone-otp/with-password` (phone + password in JSON) to issue a new OTP "
        "(delivered via your SMS/channel integration; not returned in the API), then `POST /owners/verify-phone` "
        "with the code; do not register again.\n"
        "- `registered=true` and `is_verified_phone=true` → use `POST /clients/auth/login` with "
        "`account_type=owner` (login is rejected until the phone is verified).\n\n"
        "Unauthenticated; no side effects on the database."
    ),
)
def check_phone(db: DbSession, phone: str = Query(..., min_length=1)):
    registered, verified = _svc(db).check_phone_status(phone.strip())
    return json_success(
        OwnerCheckPhoneResponse(registered=registered, is_verified_phone=verified).model_dump(
            mode="json"
        ),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/register",
    response_model=ApiResponse[CompanyOwnerPublicRead],
    summary="Step 2: Register owner (before verification)",
    description=(
        "Second step after Step 1 succeeded (`registered=false`).\n\n"
        "Creates an owner account with:\n"
        "- `is_verified_phone=false`\n"
        "- `account_status=pending_verification`\n"
        "- `join_date=now`\n\n"
        "Then proceed to Step 3 (Verify phone)."
    ),
)
def register_owner(data: OwnerRegisterRequest, db: DbSession):
    try:
        row = _svc(db).register(data)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        CompanyOwnerPublicRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/resend-phone-otp/with-password",
    response_model=ApiResponse[dict],
    summary="Refresh owner OTP (phone + password)",
    description=(
        "For flows **without** a Bearer token (e.g. after register, before login).\n\n"
        "Body: `phone` and `password` (same as registration). Generates a new OTP, hashes it, and stores it as "
        "``otp_hash``. The plain OTP is **not** returned (integrate SMS or another channel to deliver it).\n\n"
        "``is_verified_phone`` is unchanged.\n\n"
        "Refused if credentials are wrong, the phone is unknown, or the account is suspended, blocked, or deleted."
    ),
)
def resend_owner_phone_otp_with_password(data: OwnerResendOtpWithPasswordRequest, db: DbSession):
    try:
        _svc(db).resend_otp_with_password(data.phone, data.password)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success({}, message=ResponseEnum.SUCCESS.value)


@router.post(
    "/resend-phone-otp",
    response_model=ApiResponse[dict],
    summary="Refresh owner OTP (Bearer)",
    description=(
        "Authenticated **company owner** access token. Subject must be ``companies_owners.id``.\n\n"
        "Generates a new OTP, hashes it, and stores it as ``otp_hash``. The plain OTP is **not** returned.\n\n"
        "Profile fields are unchanged.\n\n"
        "Refused if the account is suspended, blocked, or deleted."
    ),
)
def resend_owner_phone_otp(current: CurrentOwnerRequired, db: DbSession):
    try:
        _svc(db).resend_otp_for_owner_id(current["user_id"])
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success({}, message=ResponseEnum.SUCCESS.value)


@router.post(
    "/verify-phone",
    response_model=ApiResponse[CompanyOwnerPublicRead],
    summary="Step 3: Verify owner phone",
    description=(
        "Last step of registration.\n\n"
        "Verifies the OTP and activates the account:\n"
        "- sets `is_verified_phone=true`\n"
        "- sets `account_status=active`\n"
        "- clears `otp_hash` (one-time use)\n\n"
        "After success, the user can login using `/clients/auth/login` with `account_type=owner`."
    ),
)
def verify_owner_phone(data: OwnerVerifyPhoneRequest, db: DbSession):
    try:
        row = _svc(db).verify_phone(phone=data.phone, otp=data.otp)
    except ValueError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        CompanyOwnerPublicRead.model_validate(row).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )

