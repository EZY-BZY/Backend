"""Audit log routes. Mount under /api/v1. Require audit:view permission."""

from uuid import UUID

from fastapi import APIRouter

from app.common.api_response import ApiResponse, json_error, json_success
from app.common.allenums import ResponseEnum
from app.modules.audit_logs.dependencies import AuditLogServiceDep
from app.modules.audit_logs.schemas import AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit_logs"])


@router.get("", response_model=ApiResponse[list[AuditLogRead]])
def list_audit_logs(
    service: AuditLogServiceDep,
    company_id: UUID | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> ApiResponse[list[AuditLogRead]]:
    """List audit logs for current company. In production: company_id from auth."""
    if not company_id:
        return json_error(
            ResponseEnum.FAIL.value,
            http_status=400,
            details="company_id required (from auth in production)",
        )
    logs = service.list_by_company(company_id, skip=skip, limit=limit, action=action)
    items = [
        AuditLogRead(
            id=UUID(log.id),
            actor_user_id=UUID(log.actor_user_id) if log.actor_user_id else None,
            company_id=UUID(log.company_id) if log.company_id else None,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            metadata=log.metadata_,
            note=log.note,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]
    return json_success([i.model_dump() for i in items], message=ResponseEnum.SUCCESS.value)
