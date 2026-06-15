import json

import pytest

from src.agents.tools import TransferMoneyTool
from src.data.bootstrap import build_data_stores
from src.data.tool_execution import ToolExecutionService
from src.security.pii import mask_pii


@pytest.fixture
def stores():
    return build_data_stores("sqlite+pysqlite:///:memory:")


def test_conversation_and_message_persistence(stores):
    conversation = stores.conversation_repo.create(
        user_id="user-1",
        conversation_id="conv-100",
    )
    stores.message_repo.add_message(
        conversation_id=conversation.id,
        role="user",
        content="Hello",
    )

    messages = stores.message_repo.list_by_conversation(conversation.id)
    assert len(messages) == 1
    assert messages[0].role == "user"


def test_audit_log_masks_pii(stores):
    row = stores.audit_repo.append(
        actor="user-1",
        action="tool_call_completed",
        risk_level="high",
        details={
            "email": "customer@ing.com",
            "iban": "TR330006100519786457841326",
            "phone": "+90 532 000 00 00",
        },
    )

    payload = json.loads(row.details_json)
    assert "[EMAIL_REDACTED]" in payload["email"]
    assert "[IBAN_REDACTED]" in payload["iban"]
    assert "[PHONE_REDACTED]" in payload["phone"]


@pytest.mark.asyncio
async def test_tool_call_idempotency_blocks_duplicate_execution(stores):
    service: ToolExecutionService = stores.tool_execution_service
    tool = TransferMoneyTool()

    first_result, first_replayed = await service.execute_tool(
        conversation_id="conv-1",
        tool=tool,
        tool_name=tool.name,
        arguments={"amount": 1000, "destination": "TR330006100519786457841326"},
        actor="user-1",
        idempotency_key="idem-123",
        approval_id="approval-1",
        risk_level="high",
    )
    second_result, second_replayed = await service.execute_tool(
        conversation_id="conv-1",
        tool=tool,
        tool_name=tool.name,
        arguments={"amount": 1000, "destination": "TR330006100519786457841326"},
        actor="user-1",
        idempotency_key="idem-123",
        approval_id="approval-1",
        risk_level="high",
    )

    assert first_replayed is False
    assert second_replayed is True
    assert first_result.output == second_result.output

    stored = stores.tool_call_repo.get_by_idempotency_key("idem-123")
    assert stored is not None
    assert stored.status == "completed"
    assert "[IBAN_REDACTED]" in stored.output_summary or "Transfer scheduled" in stored.output_summary


def test_mask_pii_examples():
    raw = "Contact me at alice@bank.com or +905321112233"
    masked = mask_pii(raw)
    assert "alice@bank.com" not in masked
    assert "[EMAIL_REDACTED]" in masked
