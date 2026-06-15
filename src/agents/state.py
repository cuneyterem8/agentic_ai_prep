from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from src.agents.policies import UserRole
from src.agents.tools import ToolResult
from src.llm.structured_output import IntentClassification, RiskLevel
from src.observability.traces import TraceSummary


class WorkflowStatus(str, Enum):
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    action: str
    actor: str
    risk_level: RiskLevel = RiskLevel.LOW
    details: dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    conversation_id: str
    tenant_id: str = "default"
    user_role: UserRole = UserRole.CUSTOMER
    customer_message: str
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))

    classification: IntentClassification | None = None
    retrieved_doc_ids: list[str] = Field(default_factory=list)
    retrieved_context: str = ""
    selected_tool: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)

    needs_human_approval: bool = False
    approval_granted: bool = False
    approval_id: str | None = None

    tool_result: ToolResult | None = None
    tool_executed: bool = False
    final_answer: str = ""
    audit_events: list[AuditEvent] = Field(default_factory=list)

    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_node: str = "start"
    steps_completed: list[str] = Field(default_factory=list)
    error: str | None = None


class WorkflowResult(BaseModel):
    run_id: str
    conversation_id: str
    status: WorkflowStatus
    final_answer: str
    needs_human_approval: bool
    approval_id: str | None = None
    selected_tool: str | None = None
    audit_events: list[AuditEvent]
    steps_completed: list[str]
    trace_id: str | None = None
    trace_summary: TraceSummary | None = None
