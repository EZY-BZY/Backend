"""Business logic for company owners."""

from __future__ import annotations

import logging
import secrets
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.allenums import OwnerAccountStatus
from app.db.base import utc_now
from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password
from app.modules.companies_owners.models import CompanyOwner
from app.modules.companies_owners.repository import CompanyOwnerRepository
from app.modules.companies_owners.schemas import (
    OwnerRegisterRequest,
    OwnersListFilters,
)
from app.services.sms_service import (
    check_phone_verification,
    owner_otp_uses_twilio_verify,
    send_otp_sms,
)

logger = logging.getLogger(__name__)

_PG_UNIQUE_VIOLATION = "23505"
_PG_NOT_NULL_VIOLATION = "23502"
_PG_CHECK_VIOLATION = "23514"


def _register_integrity_user_message(exc: IntegrityError) -> str:
    """Map PostgreSQL integrity errors to a safe, actionable API message."""
    orig = getattr(exc, "orig", None)
    if orig is None:
        return "Could not register owner (duplicate or constraint violation)."

    pgcode = getattr(orig, "pgcode", None)
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None) if diag else None
    column = getattr(diag, "column_name", None) if diag else None
    detail_lower = str(orig).lower()

    if pgcode == _PG_UNIQUE_VIOLATION or "unique constraint" in detail_lower:
        c = (constraint or "").lower()
        if "phone" in c or "uq_companies_owners_phone" in detail_lower:
            return "Phone is already registered."
        return "Could not register owner (duplicate or constraint violation)."

    if pgcode == _PG_NOT_NULL_VIOLATION or "not null violation" in detail_lower:
        logger.warning("Owner register NOT NULL violation column=%s", column)
        if column and "forgot_password" in column:
            return (
                "Registration failed: database is missing column defaults. "
                "Run `alembic upgrade head` on the server (migration 029+)."
            )
        return (
            f"Registration failed (required field missing{f': {column}' if column else ''}). "
            "Ensure the database is migrated to the latest revision."
        )

    if pgcode == _PG_CHECK_VIOLATION:
        return "Registration failed (invalid data for new account)."

    if "uq_companies_owners_phone" in detail_lower or "ix_companies_owners_phone" in detail_lower:
        return "Phone is already registered."

    return "Could not register owner (duplicate or constraint violation)."


class CompanyOwnerService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyOwnerRepository(db)

    def is_phone_registered(self, phone: str) -> bool:
        return self._repo.get_by_phone(phone) is not None

    def check_phone_status(self, phone: str) -> tuple[bool, bool]:
        """Returns (registered, is_verified_phone). Unregistered phones use is_verified_phone=False."""
        row = self._repo.get_by_phone(phone)
        if row is None:
            return False, False
        return True, row.is_verified_phone

    def get_by_phone(self, phone: str) -> CompanyOwner | None:
        return self._repo.get_by_phone(phone)

    def register(self, data: OwnerRegisterRequest) -> CompanyOwner:
        existing = self._repo.get_by_phone(data.phone)
        if existing and existing.is_verified_phone:
            raise ValueError("Phone is already registered.")

        if owner_otp_uses_twilio_verify():
            otp_plain_for_sms = ""
            otp_hash = None
        else:
            otp_plain_for_sms = self._new_owner_otp_plain()
            otp_hash = get_password_hash(otp_plain_for_sms)

        created_at = utc_now()
        pwd_hash = get_password_hash(data.password)
        email_val = str(data.email) if data.email is not None else None

        if existing:
            existing.name = data.name
            existing.email = email_val
            existing.password_hash = pwd_hash
            existing.otp_hash = otp_hash
            existing.last_accepted_terms_date = created_at
            existing.is_verified_phone = False
            existing.account_status = OwnerAccountStatus.PENDING_VERIFICATION.value
            existing.forgot_password_verify_attempts = 0
            existing.forgot_password_resend_attempts = 0
            existing.forgot_password_otp_hash = None
            existing.forgot_password_otp_expires_at = None
            existing.forgot_password_otp_verified_at = None
            existing.forgot_password_last_sent_at = None
            saved = self._repo.update(existing)
            send_otp_sms(to_phone=saved.phone, otp_code=otp_plain_for_sms, name=saved.name)
            return saved

        owner_row = CompanyOwner(
            name=data.name,
            phone=data.phone,
            email=email_val,
            password_hash=pwd_hash,
            otp_hash=otp_hash,
            last_accepted_terms_date=created_at,
            is_verified_phone=False,
            account_status=OwnerAccountStatus.PENDING_VERIFICATION.value,
            forgot_password_verify_attempts=0,
            forgot_password_resend_attempts=0,
        )
        try:
            created = self._repo.create(owner_row)
        except IntegrityError as e:
            self._db.rollback()
            logger.warning("Owner register failed: %s", e.orig)
            raise ValueError(_register_integrity_user_message(e)) from e

        send_otp_sms(to_phone=created.phone, otp_code=otp_plain_for_sms, name=created.name)
        return created

    def verify_phone(self, *, phone: str, otp: str) -> CompanyOwner:
        row = self._repo.get_by_phone(phone)
        if not row:
            raise ValueError("Owner not found.")

        if row.is_verified_phone:
            raise ValueError("Phone is already verified.")

        if owner_otp_uses_twilio_verify():
            if not check_phone_verification(to_phone=phone, code=otp):
                raise ValueError("Invalid OTP.")
        else:
            if not row.otp_hash:
                raise ValueError("OTP is not available or already used.")

            if not verify_password(otp, row.otp_hash):
                raise ValueError("Invalid OTP.")
        #TODO: Make the OTP code null after successful verification.

        row.is_verified_phone = True
        row.account_status = OwnerAccountStatus.ACTIVE.value
        row.otp_hash = None
        return self._repo.update(row)

    def _ensure_can_issue_otp(self, row: CompanyOwner) -> None:
        if row.account_status in (
            OwnerAccountStatus.SUSPENDED.value,
            OwnerAccountStatus.BLOCKED.value,
            OwnerAccountStatus.DELETED.value,
        ):
            raise ValueError("Account cannot refresh OTP.")

    def _new_owner_otp_plain(self) -> str:
        settings = get_settings()
        if settings.environment != "production":
            return "000000"
        return f"{secrets.randbelow(1_000_000):06d}"

    def _issue_otp_on_row(self, row: CompanyOwner) -> str:
        self._ensure_can_issue_otp(row)
        otp_plain = self._new_owner_otp_plain()
        row.otp_hash = get_password_hash(otp_plain)
        self._repo.update(row)
        return otp_plain

    def resend_otp_for_owner_id(self, owner_id: str) -> None:
        """Bearer token path: subject is companies_owners.id. OTP is stored hashed only (not returned)."""
        row = self._repo.get_by_id(owner_id)
        if not row:
            raise ValueError("Owner not found.")
        if owner_otp_uses_twilio_verify():
            send_otp_sms(to_phone=row.phone, otp_code="", name=row.name)
            return
        otp_plain = self._issue_otp_on_row(row)
        send_otp_sms(to_phone=row.phone, otp_code=otp_plain, name=row.name)

    def resend_otp_with_password(self, phone: str, password: str) -> None:
        """Phone + password path (e.g. before login / without token). OTP is stored hashed only (not returned)."""
        row = self._repo.get_by_phone(phone.strip())
        if not row:
            raise ValueError("Owner not found.")
        if not verify_password(password, row.password_hash):
            raise ValueError("Invalid phone or password.")
        if owner_otp_uses_twilio_verify():
            send_otp_sms(to_phone=row.phone, otp_code="", name=row.name)
            return
        otp_plain = self._issue_otp_on_row(row)
        send_otp_sms(to_phone=row.phone, otp_code=otp_plain, name=row.name)

    def authenticate_owner(self, *, phone: str, password: str) -> CompanyOwner:
        row = self._repo.get_by_phone(phone)
        if not row or not verify_password(password, row.password_hash):
            raise ValueError("Invalid phone or password.")
        if not row.is_verified_phone:
            raise ValueError("Phone is not verified.")
        if row.account_status != OwnerAccountStatus.ACTIVE.value:
            raise ValueError("Account is not active.")
        return row

    def list(self, filters: OwnersListFilters) -> list[CompanyOwner]:
        return self._repo.list_filtered(
            account_status=filters.account_status,
            is_verified_phone=filters.is_verified_phone,
            join_date_from=filters.join_date_from,
            join_date_to=filters.join_date_to,
        )

    def get_by_id(self, owner_id: str) -> CompanyOwner | None:
        return self._repo.get_by_id(owner_id)

    def search(self, query: str) -> list[CompanyOwner]:
        owner_id: str | None = None
        try:
            owner_id = str(UUID(query))
        except Exception:
            owner_id = None
        return self._repo.search(query, owner_id=owner_id)

    def set_status(self, *, owner_id: str, status: OwnerAccountStatus, actor_id: str) -> CompanyOwner | None:
        row = self._repo.get_by_id(owner_id)
        if not row:
            return None
        row.account_status = status.value
        row.updated_by = actor_id
        return self._repo.update(row)

