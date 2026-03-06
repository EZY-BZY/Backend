"""Audit logs module. Records sensitive actions for compliance."""

from app.modules.audit_logs.service import AuditLogService

__all__ = ["AuditLogService"]
