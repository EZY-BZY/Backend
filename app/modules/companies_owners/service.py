"""Business logic for company owners."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.allenums import OwnerAccountStatus
from app.core.security import get_password_hash, verify_password
from app.modules.companies_owners.models import CompanyOwner
from app.modules.companies_owners.repository import CompanyOwnerRepository
from app.modules.companies_owners.schemas import (
    OwnerRegisterRequest,
    OwnersListFilters,
)


class CompanyOwnerService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = CompanyOwnerRepository(db)

    def is_phone_registered(self, phone: str) -> bool:
        return self._repo.get_by_phone(phone) is not None

    def get_by_phone(self, phone: str) -> CompanyOwner | None:
        return self._repo.get_by_phone(phone)

    def register(self, data: OwnerRegisterRequest) -> CompanyOwner:
        if self._repo.get_by_phone(data.phone):
            raise ValueError("Phone is already registered.")

        # OTP is fixed for now, later we will use a more secure OTP generation method.
        # TODO: Implement a more secure OTP generation method, and Integrate with OTP service.
        otp_code = "000000"

        row = CompanyOwner(
            name=data.name,
            phone=data.phone,
            email=str(data.email) if data.email is not None else None,
            password_hash=get_password_hash(data.password),
            otp_hash=get_password_hash(otp_code),
            is_verified_phone=False,
            account_status=OwnerAccountStatus.PENDING_VERIFICATION.value,
        )
        try:
            return self._repo.create(row)
        except IntegrityError as e:
            self._db.rollback()
            raise ValueError("Could not register owner (duplicate or constraint violation).") from e

    def verify_phone(self, *, phone: str, otp: str) -> CompanyOwner:
        row = self._repo.get_by_phone(phone)
        if not row:
            raise ValueError("Owner not found.")

        if row.is_verified_phone:
            raise ValueError("Phone is already verified.")

        if not row.otp_hash:
            raise ValueError("OTP is not available or already used.")

        if not verify_password(otp, row.otp_hash):
            raise ValueError("Invalid OTP.")
        #TODO: Make the OTP code null after successful verification.

        row.is_verified_phone = True
        row.account_status = OwnerAccountStatus.ACTIVE.value
        row.otp_hash = None
        return self._repo.update(row)

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

