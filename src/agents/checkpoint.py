from src.agents.state import AgentState, AuditEvent, WorkflowStatus
from src.llm.structured_output import RiskLevel


def append_audit(
    state: AgentState,
    *,
    action: str,
    actor: str,
    risk_level: RiskLevel = RiskLevel.LOW,
    details: dict | None = None,
) -> None:
    state.audit_events.append(
        AuditEvent(
            action=action,
            actor=actor,
            risk_level=risk_level,
            details=details or {},
        )
    )


def mark_step_complete(state: AgentState, node_name: str) -> None:
    if node_name not in state.steps_completed:
        state.steps_completed.append(node_name)
    state.current_node = node_name


def to_checkpoint(state: AgentState) -> dict:
    return state.model_dump()


def from_checkpoint(payload: dict) -> AgentState:
    return AgentState.model_validate(payload)
