"""Audit log repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit_logs.models import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_by_company(
        self,
        company_id: UUID | str,
        *,
        skip: int = 0,
        limit: int = 100,
        action: str | None = None,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.company_id == str(company_id))
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
