import json

import pytest

from src.agents.policies import (
    PolicyDecision,
    UserRole,
    can_execute_tool,
    evaluate_tool_permission,
    is_read_only_tool,
)
from src.agents.tools import KnowledgeSearchTool, TransferMoneyTool
from src.agents.workflow import CustomerSupportWorkflow, clear_checkpoints
from src.data.bootstrap import build_data_stores
from src.llm.mock_client import MockLLMClient
from src.llm.structured_output import IntentClassification, IntentType, RiskLevel
from src.security.audit import (
    build_tool_audit_event,
    minimize_tool_arguments,
    to_persistence_payload,
)
from src.security.pii import mask_pii


def _classification(
    intent: IntentType,
    risk: RiskLevel,
    approval: bool,
) -> IntentClassification:
    return IntentClassification(
        intent=intent,
        risk_level=risk,
        needs_human_approval=approval,
    )


def test_customer_role_denied_unauthorized_tool():
    result = evaluate_tool_permission(
        user_id="user-1",
        tool_name="delete_account",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
        user_role=UserRole.CUSTOMER,
    )
    assert result.decision == PolicyDecision.DENY


def test_customer_can_use_read_only_knowledge_search():
    result = can_execute_tool(
        user_id="user-1",
        tool_name="knowledge_search",
        classification=_classification(IntentType.KNOWLEDGE_QUESTION, RiskLevel.LOW, False),
        approval_granted=False,
        user_role=UserRole.CUSTOMER,
    )
    assert result.decision == PolicyDecision.ALLOW
    assert is_read_only_tool("knowledge_search") is True


def test_customer_transfer_requires_human_approval():
    result = can_execute_tool(
        user_id="user-1",
        tool_name="transfer_money",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
        approval_granted=False,
        user_role=UserRole.CUSTOMER,
    )
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_customer_transfer_allowed_after_approval_with_elevated_role():
    result = can_execute_tool(
        user_id="user-1",
        tool_name="transfer_money",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
        approval_granted=True,
        user_role=UserRole.CUSTOMER,
    )
    assert result.decision == PolicyDecision.ALLOW
    assert result.effective_role == UserRole.SUPPORT_AGENT


def test_support_agent_can_execute_transfer_with_approval():
    result = can_execute_tool(
        user_id="agent-1",
        tool_name="transfer_money",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
        approval_granted=True,
        user_role=UserRole.SUPPORT_AGENT,
    )
    assert result.decision == PolicyDecision.ALLOW


def test_minimize_tool_arguments_masks_pii_and_drops_extra_fields():
    args = minimize_tool_arguments(
        "transfer_money",
        {
            "amount": 1000,
            "destination": "TR330006100519786457841326",
            "customer_email": "secret@example.com",
        },
    )
    assert "customer_email" not in args
    assert args["destination"] == "[IBAN_REDACTED]"
    assert args["amount"] == "1000"


def test_build_tool_audit_event_contains_compliance_fields():
    event = build_tool_audit_event(
        actor="user-1",
        tenant_id="tenant-a",
        action="tool_call_completed",
        tool_name="transfer_money",
        arguments={
            "amount": 80000,
            "destination": "TR330006100519786457841326",
        },
        approval_id="approval-123",
        result_status="success",
        risk_level="high",
    )
    payload = to_persistence_payload(event)
    assert payload["tenant_id"] == "tenant-a"
    assert payload["approval_id"] == "approval-123"
    assert payload["tool_name"] == "transfer_money"
    assert "[IBAN_REDACTED]" in payload["args_summary"]["destination"]


@pytest.mark.asyncio
async def test_tool_execution_audit_log_does_not_store_raw_pii():
    stores = build_data_stores("sqlite+pysqlite:///:memory:")
    service = stores.tool_execution_service
    tool = TransferMoneyTool()

    await service.execute_tool(
        conversation_id="conv-sec-1",
        tool=tool,
        tool_name="transfer_money",
        arguments={
            "amount": 1000,
            "destination": "TR330006100519786457841326",
        },
        actor="user-1",
        tenant_id="tenant-a",
        idempotency_key="idem-1",
        approval_id="approval-1",
        risk_level="high",
    )

    rows = stores.audit_repo.list_recent(limit=5)
    assert rows
    details = json.loads(rows[0].details_json)
    serialized = json.dumps(details)
    assert "TR330006100519786457841326" not in serialized
    assert details["tenant_id"] == "tenant-a"
    assert details["args_summary"]["destination"] == "[IBAN_REDACTED]"


@pytest.mark.asyncio
async def test_workflow_blocks_customer_transfer_without_approval():
    clear_checkpoints()
    workflow = CustomerSupportWorkflow(MockLLMClient())
    result = await workflow.run(
        user_id="user-1",
        conversation_id="conv-sec-2",
        customer_message="Hesabımdan 80000 TL transfer et",
        user_role=UserRole.CUSTOMER,
    )
    assert result.status.value == "awaiting_approval"
    assert result.needs_human_approval is True


@pytest.mark.asyncio
async def test_knowledge_search_tool_is_read_only_metadata():
    tool = KnowledgeSearchTool()
    result = await tool.run({"query": "password reset policy"})
    assert result.metadata.get("read_only") is True
    assert mask_pii(result.output) == result.output
