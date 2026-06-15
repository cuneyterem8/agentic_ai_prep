import pytest

from src.agents.policies import (
    PolicyDecision,
    can_execute_tool,
    evaluate_tool_permission,
)
from src.agents.workflow import CustomerSupportWorkflow, clear_checkpoints
from src.llm.mock_client import MockLLMClient
from src.llm.structured_output import IntentClassification, IntentType, RiskLevel


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


def test_deny_unknown_tool():
    result = evaluate_tool_permission(
        user_id="user-1",
        tool_name="delete_account",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
    )

    assert result.decision == PolicyDecision.DENY


def test_transfer_requires_approval_without_grant():
    result = can_execute_tool(
        user_id="user-1",
        tool_name="transfer_money",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
        approval_granted=False,
    )

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_transfer_allowed_after_approval():
    result = can_execute_tool(
        user_id="user-1",
        tool_name="transfer_money",
        classification=_classification(IntentType.ACCOUNT_ACTION, RiskLevel.HIGH, True),
        approval_granted=True,
    )

    assert result.decision == PolicyDecision.ALLOW


def test_knowledge_search_allowed_without_approval():
    result = can_execute_tool(
        user_id="user-1",
        tool_name="knowledge_search",
        classification=_classification(IntentType.KNOWLEDGE_QUESTION, RiskLevel.LOW, False),
        approval_granted=False,
    )

    assert result.decision == PolicyDecision.ALLOW


def test_unknown_intent_denies_tool_execution():
    result = evaluate_tool_permission(
        user_id="user-1",
        tool_name="knowledge_search",
        classification=_classification(IntentType.UNKNOWN, RiskLevel.LOW, False),
    )

    assert result.decision == PolicyDecision.DENY


@pytest.mark.asyncio
async def test_workflow_knowledge_question_completes_without_approval():
    clear_checkpoints()
    workflow = CustomerSupportWorkflow(MockLLMClient())

    result = await workflow.run(
        user_id="user-1",
        conversation_id="conv-1",
        customer_message="Şifre sıfırlama policy nedir?",
    )

    assert result.status.value == "completed"
    assert result.selected_tool == "knowledge_search"
    assert "classify_intent" in result.steps_completed
    assert "audit_log" in result.steps_completed


@pytest.mark.asyncio
async def test_workflow_transfer_waits_for_approval():
    clear_checkpoints()
    workflow = CustomerSupportWorkflow(MockLLMClient())

    result = await workflow.run(
        user_id="user-1",
        conversation_id="conv-2",
        customer_message="Hesabımdan 80000 TL transfer et",
    )

    assert result.status.value == "awaiting_approval"
    assert result.needs_human_approval is True
    assert result.selected_tool == "transfer_money"
    assert result.approval_id is not None


@pytest.mark.asyncio
async def test_workflow_resumes_after_approval():
    clear_checkpoints()
    workflow = CustomerSupportWorkflow(MockLLMClient())

    first = await workflow.run(
        user_id="user-1",
        conversation_id="conv-3",
        customer_message="Hesabımdan 80000 TL transfer et",
    )

    resumed = await workflow.run(
        user_id="user-1",
        conversation_id="conv-3",
        customer_message="Hesabımdan 80000 TL transfer et",
        run_id=first.run_id,
        approval_granted=True,
        approval_id=first.approval_id,
    )

    assert resumed.status.value == "completed"
    assert "execute_tool" in resumed.steps_completed
    assert "Transfer scheduled" in resumed.final_answer


@pytest.mark.asyncio
async def test_workflow_idempotent_tool_execution_on_resume():
    clear_checkpoints()
    workflow = CustomerSupportWorkflow(MockLLMClient())

    first = await workflow.run(
        user_id="user-1",
        conversation_id="conv-4",
        customer_message="Hesabımdan 80000 TL transfer et",
    )

    resumed = await workflow.run(
        user_id="user-1",
        conversation_id="conv-4",
        customer_message="Hesabımdan 80000 TL transfer et",
        run_id=first.run_id,
        approval_granted=True,
        approval_id=first.approval_id,
    )

    execute_events = [
        event for event in resumed.audit_events if event.action == "execute_tool"
    ]
    assert len(execute_events) == 1
