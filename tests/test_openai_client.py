from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.common.config import Settings
from src.common.errors import LLMProviderError, ValidationError
from src.llm.base import Message, MessageRole
from src.llm.fallback_client import FallbackLLMClient
from src.llm.factory import create_llm_client
from src.llm.mock_client import MockLLMClient
from src.llm.openai_client import OpenAIClient
from src.llm.tool_calling import parse_tool_calls_payload, validate_tool_calls


def test_factory_uses_mock_without_api_key():
    settings = Settings(_env_file=None, llm_provider="openai", openai_api_key=None)
    client = create_llm_client(settings)
    assert isinstance(client, MockLLMClient)


def test_factory_uses_openai_with_fallback_when_configured():
    settings = Settings(
        _env_file=None,
        llm_provider="openai",
        openai_api_key="test-key",
        openai_model="gpt-4o",
        openai_fallback_model="gpt-4o-mini",
    )
    client = create_llm_client(settings)
    assert isinstance(client, FallbackLLMClient)


def test_parse_tool_calls_payload():
    payload = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "knowledge_search",
                                "arguments": '{"query":"password reset"}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    parsed = parse_tool_calls_payload(payload)
    assert len(parsed.tool_calls) == 1
    assert parsed.tool_calls[0].name == "knowledge_search"
    assert parsed.tool_calls[0].arguments["query"] == "password reset"


def test_validate_tool_calls_rejects_unknown_tool():
    payload = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "delete_account",
                                "arguments": "{}",
                            },
                        }
                    ]
                }
            }
        ]
    }
    parsed = parse_tool_calls_payload(payload)

    with pytest.raises(ValidationError):
        validate_tool_calls(parsed, allowed_tools={"knowledge_search"})


@pytest.mark.asyncio
async def test_fallback_client_uses_secondary_on_primary_failure():
    primary = MockLLMClient(default_response="primary")
    fallback = MockLLMClient(default_response="fallback")

    async def failing_complete(messages):
        raise LLMProviderError("primary down")

    primary.complete = failing_complete  # type: ignore[method-assign]

    client = FallbackLLMClient(primary=primary, fallback=fallback)
    response = await client.complete(
        [Message(role=MessageRole.USER, content="hello")]
    )

    assert "fallback" in response.content
    assert response.model.startswith("fallback:")


@pytest.mark.asyncio
async def test_openai_client_maps_response():
    mock_response = MagicMock()
    mock_response.model = "gpt-4o"
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "OpenAI cevap"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    mock_create = AsyncMock(return_value=mock_response)

    with patch("src.llm.openai_client.AsyncOpenAI") as mock_openai_cls:
        mock_openai_cls.return_value.chat.completions.create = mock_create
        client = OpenAIClient(api_key="test-key", model="gpt-4o")

        response = await client.complete(
            [Message(role=MessageRole.USER, content="test")]
        )

    assert response.content == "OpenAI cevap"
    assert response.model == "gpt-4o"
    assert response.usage.total_tokens == 15
    mock_create.assert_awaited_once()
