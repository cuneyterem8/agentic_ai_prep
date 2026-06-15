from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from src.common.logging import get_correlation_id
from src.observability.traces import get_trace
from src.security.pii import mask_mapping, mask_pii

TOOL_ARG_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "knowledge_search": ("query",),
    "transfer_money": ("amount", "destination"),
}


class ComplianceAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    actor: str
    tenant_id: str = "default"
    action: str
    tool_name: str | None = None
    args_summary: dict[str, Any] = Field(default_factory=dict)
    approval_id: str | None = None
    result_status: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    risk_level: str = "low"
    metadata: dict[str, Any] = Field(default_factory=dict)


def minimize_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, str]:
    """Data minimization — sadece allowlisted argümanlar, maskelenmiş."""
    allowed = TOOL_ARG_ALLOWLIST.get(tool_name, ())
    minimized: dict[str, str] = {}
    for key in allowed:
        if key in arguments and arguments[key] not in (None, ""):
            minimized[key] = mask_pii(str(arguments[key]))
    return minimized


def build_tool_audit_event(
    *,
    actor: str,
    tenant_id: str,
    action: str,
    tool_name: str,
    arguments: dict[str, Any],
    approval_id: str | None = None,
    result_status: str | None = None,
    risk_level: str = "low",
    metadata: dict[str, Any] | None = None,
) -> ComplianceAuditEvent:
    trace = get_trace()
    return ComplianceAuditEvent(
        actor=actor,
        tenant_id=tenant_id,
        action=action,
        tool_name=tool_name,
        args_summary=minimize_tool_arguments(tool_name, arguments),
        approval_id=approval_id,
        result_status=result_status,
        trace_id=trace.trace_id if trace else None,
        correlation_id=get_correlation_id(),
        risk_level=risk_level,
        metadata=metadata or {},
    )


def build_policy_audit_event(
    *,
    actor: str,
    tenant_id: str,
    action: str,
    risk_level: str = "low",
    details: dict[str, Any] | None = None,
    approval_id: str | None = None,
    result_status: str | None = None,
) -> ComplianceAuditEvent:
    trace = get_trace()
    return ComplianceAuditEvent(
        actor=actor,
        tenant_id=tenant_id,
        action=action,
        args_summary=mask_mapping(details or {}),
        approval_id=approval_id,
        result_status=result_status,
        trace_id=trace.trace_id if trace else None,
        correlation_id=get_correlation_id(),
        risk_level=risk_level,
    )


def to_persistence_payload(event: ComplianceAuditEvent) -> dict[str, Any]:
    """Audit repository ve structured log için normalize payload."""
    return {
        "event_id": event.event_id,
        "timestamp": event.timestamp,
        "actor": event.actor,
        "tenant_id": event.tenant_id,
        "action": event.action,
        "tool_name": event.tool_name,
        "args_summary": event.args_summary,
        "approval_id": event.approval_id,
        "result_status": event.result_status,
        "trace_id": event.trace_id,
        "correlation_id": event.correlation_id,
        "risk_level": event.risk_level,
        "metadata": event.metadata,
    }


def to_log_extra(event: ComplianceAuditEvent) -> dict[str, Any]:
    payload = to_persistence_payload(event)
    payload["event"] = "compliance_audit"
    return payload
