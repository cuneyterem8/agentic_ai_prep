import pytest

from src.common.config import Settings
from src.llm.base import Message, MessageRole
from src.llm.factory import create_llm_client
from src.llm.mock_client import MockLLMClient
from src.llm.service import generate_chat_response


@pytest.mark.asyncio
async def test_mock_client_returns_deterministic_response():
    client = MockLLMClient(model="mock-gpt-test")
    messages = [Message(role=MessageRole.USER, content="Merhaba")]

    response = await client.complete(messages)

    assert response.model == "mock-gpt-test"
    assert "Merhaba" in response.content
    assert response.usage.prompt_tokens > 0
    assert response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_mock_client_echo_prefix():
    client = MockLLMClient()
    messages = [Message(role=MessageRole.USER, content="echo: deterministic output")]

    response = await client.complete(messages)

    assert response.content == "deterministic output"


@pytest.mark.asyncio
async def test_generate_chat_response_uses_injected_client():
    client = MockLLMClient(default_response="Service reply")
    messages = [Message(role=MessageRole.USER, content="Test")]

    response = await generate_chat_response(messages, client, timeout_seconds=2.0)

    assert "Service reply" in response.content
    assert response.model == "mock-gpt"


@pytest.mark.asyncio
async def test_factory_returns_mock_client_without_api_key():
    settings = Settings(_env_file=None, llm_provider="mock", openai_api_key=None)
    client = create_llm_client(settings)

    response = await client.complete(
        [Message(role=MessageRole.USER, content="factory test")]
    )

    assert response.model.startswith("mock-")
    assert "factory test" in response.content
