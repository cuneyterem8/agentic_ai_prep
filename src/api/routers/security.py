import json

from fastapi import APIRouter, Depends, Query

from src.api.schemas import AuditLogEntryResponse, AuditLogListResponse
from src.data.bootstrap import get_data_stores

router = APIRouter(prefix="/v1/security", tags=["security"])


@router.get("/audit/recent", response_model=AuditLogListResponse)
async def list_recent_audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
) -> AuditLogListResponse:
    stores = get_data_stores()
    rows = stores.audit_repo.list_recent(limit=limit)
    entries = []
    for row in rows:
        try:
            details = json.loads(row.details_json)
        except json.JSONDecodeError:
            details = {"raw": row.details_json}
        entries.append(
            AuditLogEntryResponse(
                id=row.id,
                actor=row.actor,
                action=row.action,
                risk_level=row.risk_level,
                details=details,
                correlation_id=row.correlation_id,
                created_at=row.created_at.isoformat(),
            )
        )
    return AuditLogListResponse(entries=entries)
