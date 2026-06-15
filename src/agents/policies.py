from enum import Enum

from pydantic import BaseModel

from src.llm.structured_output import IntentClassification, IntentType, RiskLevel


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class UserRole(str, Enum):
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    ADMIN = "admin"


class PolicyResult(BaseModel):
    decision: PolicyDecision
    reason: str
    risk_level: RiskLevel = RiskLevel.LOW
    effective_role: UserRole | None = None


ALLOWED_TOOLS = {
    "knowledge_search",
    "transfer_money",
}

HIGH_RISK_TOOLS = {
    "transfer_money",
}

READ_ONLY_TOOLS = {
    "knowledge_search",
}

ROLE_TOOL_MATRIX: dict[UserRole, set[str]] = {
    UserRole.CUSTOMER: {"knowledge_search"},
    UserRole.SUPPORT_AGENT: {"knowledge_search", "transfer_money"},
    UserRole.ADMIN: {"knowledge_search", "transfer_money"},
}


def resolve_execution_role(
    user_role: UserRole,
    tool_name: str,
    *,
    approval_granted: bool,
) -> UserRole:
    """Human approval sonrası high-risk tool SUPPORT_AGENT yetkisiyle çalışır."""
    if approval_granted and tool_name in HIGH_RISK_TOOLS:
        return UserRole.SUPPORT_AGENT
    return user_role


def evaluate_tool_permission(
    *,
    user_id: str,
    tool_name: str,
    classification: IntentClassification | None,
    user_role: UserRole = UserRole.CUSTOMER,
    approval_granted: bool = False,
) -> PolicyResult:
    effective_role = resolve_execution_role(
        user_role,
        tool_name,
        approval_granted=approval_granted,
    )

    if tool_name not in ALLOWED_TOOLS:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            reason=f"Tool '{tool_name}' is not in allowlist",
            risk_level=RiskLevel.HIGH,
            effective_role=effective_role,
        )

    role_tools = ROLE_TOOL_MATRIX.get(effective_role, set())
    if tool_name not in role_tools:
        if (
            tool_name in HIGH_RISK_TOOLS
            and user_role == UserRole.CUSTOMER
            and not approval_granted
        ):
            return PolicyResult(
                decision=PolicyDecision.REQUIRE_APPROVAL,
                reason="High-risk tool requires human approval before customer execution",
                risk_level=RiskLevel.HIGH,
                effective_role=effective_role,
            )
        return PolicyResult(
            decision=PolicyDecision.DENY,
            reason=(
                f"Role '{effective_role.value}' is not permitted to use tool '{tool_name}'"
            ),
            risk_level=RiskLevel.HIGH,
            effective_role=effective_role,
        )

    if classification and classification.intent == IntentType.UNKNOWN:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            reason="Cannot execute tools for unknown intent",
            risk_level=RiskLevel.MEDIUM,
            effective_role=effective_role,
        )

    if tool_name in HIGH_RISK_TOOLS and not approval_granted:
        return PolicyResult(
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason="High-risk financial tool requires human approval",
            risk_level=RiskLevel.HIGH,
            effective_role=effective_role,
        )

    if classification and classification.needs_human_approval and not approval_granted:
        return PolicyResult(
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason="Classification flagged human approval",
            risk_level=classification.risk_level,
            effective_role=effective_role,
        )

    return PolicyResult(
        decision=PolicyDecision.ALLOW,
        reason="Low-risk read-only or approved action",
        risk_level=classification.risk_level if classification else RiskLevel.LOW,
        effective_role=effective_role,
    )


def can_execute_tool(
    *,
    user_id: str,
    tool_name: str,
    classification: IntentClassification | None,
    approval_granted: bool,
    user_role: UserRole = UserRole.CUSTOMER,
) -> PolicyResult:
    policy = evaluate_tool_permission(
        user_id=user_id,
        tool_name=tool_name,
        classification=classification,
        user_role=user_role,
        approval_granted=approval_granted,
    )

    if policy.decision == PolicyDecision.DENY:
        return policy

    if policy.decision == PolicyDecision.REQUIRE_APPROVAL and not approval_granted:
        return PolicyResult(
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=policy.reason,
            risk_level=policy.risk_level,
            effective_role=policy.effective_role,
        )

    if policy.decision == PolicyDecision.REQUIRE_APPROVAL and approval_granted:
        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            reason="Human approval granted",
            risk_level=policy.risk_level,
            effective_role=policy.effective_role,
        )

    return policy


def is_read_only_tool(tool_name: str) -> bool:
    return tool_name in READ_ONLY_TOOLS
