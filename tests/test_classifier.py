import pytest
from fastapi.testclient import TestClient

from src.agents.callbacks import ChainCallbackHandler
from src.agents.classifier import classify_customer_message
from src.agents.tools import KnowledgeSearchTool
from src.api.main import app
from src.common.errors import ValidationError
from src.llm.base import LLMResponse, Message, MessageRole, TokenUsage
from src.llm.mock_client import MockLLMClient
from src.llm.structured_output import IntentType, RiskLevel
from src.rag.retriever import MockRetriever


class BrokenJSONMockClient:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, messages: list[Message]) -> LLMResponse:
        self.calls += 1
        is_repair = any(
            m.role == MessageRole.SYSTEM and "fix the following text" in m.content.lower()
            for m in messages
        )
        if is_repair:
            content = (
                '{"intent":"complaint","risk_level":"medium","needs_human_approval":false}'
            )
        else:
            content = '{"intent":"complaint","risk_level":"medium"'  # invalid JSON

        return LLMResponse(content=content, model="broken-mock")

    async def stream(self, messages: list[Message]):
        if False:
            yield


@pytest.mark.asyncio
async def test_classify_complaint_message():
    client = MockLLMClient()
    result = await classify_customer_message("Müşteri şikayet ediyor", client)

    assert result.intent == IntentType.COMPLAINT
    assert result.risk_level == RiskLevel.MEDIUM


@pytest.mark.asyncio
async def test_classify_transfer_requires_approval():
    client = MockLLMClient()
    result = await classify_customer_message("Hesabımdan 80000 TL transfer et", client)

    assert result.intent == IntentType.ACCOUNT_ACTION
    assert result.risk_level == RiskLevel.HIGH
    assert result.needs_human_approval is True


@pytest.mark.asyncio
async def test_classify_repair_flow_on_broken_json():
    client = BrokenJSONMockClient()
    result = await classify_customer_message("complaint text", client, max_repairs=1)

    assert result.intent == IntentType.COMPLAINT
    assert client.calls == 2


@pytest.mark.asyncio
async def test_classify_emits_callback_trace():
    client = MockLLMClient()
    callbacks = ChainCallbackHandler()

    await classify_customer_message("policy limit nedir", client, callbacks=callbacks)

    event_names = [event.event for event in callbacks.events]
    assert "chain_start" in event_names
    assert "llm_end" in event_names
    assert "parse_success" in event_names
    assert "chain_end" in event_names


@pytest.mark.asyncio
async def test_knowledge_search_tool():
    tool = KnowledgeSearchTool()
    result = await tool.run({"query": "password reset"})

    assert result.success is True
    assert "password reset" in result.output


@pytest.mark.asyncio
async def test_mock_retriever_returns_relevant_docs():
    retriever = MockRetriever()
    docs = await retriever.retrieve("transfer approval limit", top_k=2)

    assert len(docs) >= 1
    assert any("transfer" in doc.content.lower() for doc in docs)


def test_classify_endpoint():
    client = TestClient(app)
    response = client.post(
        "/v1/classify",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "message": "Şifre sıfırlama policy nedir?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "knowledge_question"
    assert body["risk_level"] == "low"
    assert body["needs_human_approval"] is False
