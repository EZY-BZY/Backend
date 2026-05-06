"""Client-facing routes for company owner registration/verification."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.common.allenums import ResponseEnum
from app.common.api_response import ApiResponse, json_error, json_success
from app.db.session import DbSession
from app.modules.companies_owners.schemas import (
    CompanyOwnerPublicRead,
    OwnerCheckPhoneResponse,
    OwnerRegisterRequest,
    OwnerVerifyPhoneRequest,
)
from app.modules.companies_owners.service import CompanyOwnerService

router = APIRouter(prefix="/owners", tags=["Owners (clients)"])


def _svc(db: DbSession) -> CompanyOwnerService:
    return CompanyOwnerService(db)


@router.get(
    "/check-phone",
    response_model=ApiResponse[OwnerCheckPhoneResponse],
    summary="Step 1: Check if phone is registered",
    description=(
        "First step before registration.\n\n"
        "Checks whether a phone number already exists in `companies_owners`.\n\n"
        "- If `registered=true`: user should login instead of registering.\n"
        "- If `registered=false`: proceed to Step 2 (Register)."
    ),
)
def check_phone(db: DbSession, phone: str = Query(..., min_length=1)):
    registered = _svc(db).is_phone_registered(phone.strip())
    return json_success(
        OwnerCheckPhoneResponse(registered=registered).model_dump(),
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

