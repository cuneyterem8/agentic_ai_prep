import asyncio

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_llm_client
from src.api.main import app
from src.common.errors import LLMTimeoutError
from src.llm.base import LLMResponse, Message, MessageRole, TokenUsage
from src.llm.service import generate_chat_response


class SlowLLMClient:
    async def complete(self, messages: list[Message]) -> LLMResponse:
        await asyncio.sleep(2)
        return LLMResponse(content="slow", model="slow-mock")

    async def stream(self, messages: list[Message]):
        yield "slow "
        if False:
            yield


class TimeoutLLMClient:
    async def complete(self, messages: list[Message]) -> LLMResponse:
        raise LLMTimeoutError("provider timed out")

    async def stream(self, messages: list[Message]):
        if False:
            yield


@pytest.fixture
def client():
    return TestClient(app)


def test_chat_returns_mock_response(client):
    response = client.post(
        "/v1/chat",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "message": "Merhaba",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == "conv-1"
    assert "Merhaba" in body["message"]
    assert body["model"].startswith("mock-")


def test_chat_invalid_request_returns_422(client):
    response = client.post(
        "/v1/chat",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "message": "",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_chat_timeout_returns_504(client):
    app.dependency_overrides[get_llm_client] = lambda: TimeoutLLMClient()

    try:
        response = client.post(
            "/v1/chat",
            json={
                "user_id": "user-1",
                "conversation_id": "conv-1",
                "message": "timeout please",
            },
        )
        assert response.status_code == 504
        assert response.json()["error"]["code"] == "llm_timeout"
    finally:
        app.dependency_overrides.clear()


def test_chat_streaming_returns_sse(client):
    response = client.post(
        "/v1/chat",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "message": "echo: stream test",
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data:" in response.text
    assert '"done": true' in response.text.lower() or '"done":true' in response.text.replace(" ", "")


def test_agent_run_endpoint(client):
    response = client.post(
        "/v1/agent/run",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-2",
            "task": "summarize",
            "input": "Customer wants refund",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert "summarize" in body["result"].lower() or "refund" in body["result"].lower()


@pytest.mark.asyncio
async def test_generate_chat_response_timeout_from_service():
    class InstantTimeoutClient:
        async def complete(self, messages: list[Message]) -> LLMResponse:
            await asyncio.sleep(0.2)
            return LLMResponse(content="x", model="m")

        async def stream(self, messages: list[Message]):
            if False:
                yield

    with pytest.raises(LLMTimeoutError):
        await generate_chat_response(
            [Message(role=MessageRole.USER, content="hi")],
            InstantTimeoutClient(),
            timeout_seconds=0.05,
            max_attempts=1,
        )
