"""Audit logs module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.audit_logs.service import AuditLogService


def get_audit_log_service(db: DbSession) -> AuditLogService:
    return AuditLogService(db)


AuditLogServiceDep = Annotated[AuditLogService, Depends(get_audit_log_service)]
