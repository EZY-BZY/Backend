"""Audit log service. Public API: log action, list by company."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.audit_logs.models import AuditLog
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.schemas import AuditLogCreate


# Standard action names for consistency
ACTION_LOGIN = "login"
ACTION_CREATE_EMPLOYEE = "create_employee"
ACTION_BLOCK_EMPLOYEE = "block_employee"
ACTION_CREATE_ORDER = "create_order"
ACTION_CREATE_INVOICE = "create_invoice"
ACTION_REGISTER_PAYMENT = "register_payment"


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self._repo = AuditLogRepository(db)

    def log(
        self,
        actor_user_id: UUID | str | None,
        company_id: UUID | str | None,
        data: AuditLogCreate,
    ) -> AuditLog:
        """Append an audit record. Call from other modules after sensitive actions."""
        log = AuditLog(
            actor_user_id=str(actor_user_id) if actor_user_id else None,
            company_id=str(company_id) if company_id else None,
            action=data.action,
            target_type=data.target_type,
            target_id=data.target_id,
            metadata_=data.metadata,
            note=data.note,
        )
        return self._repo.create(log)

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
        action: str | None = None,
    ) -> list[AuditLog]:
        return self._repo.list_by_company(company_id, skip=skip, limit=limit, action=action)
