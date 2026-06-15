import logging
import time
from collections.abc import AsyncIterator

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, RateLimitError

from src.common.errors import LLMProviderError, LLMTimeoutError
from src.llm.base import LLMResponse, Message, TokenUsage

logger = logging.getLogger("agenticai")


class OpenAIClient:
    """Production OpenAI adapter with structured logging and error mapping."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)

    async def complete(self, messages: list[Message]) -> LLMResponse:
        started = time.perf_counter()

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": message.role.value, "content": message.content}
                    for message in messages
                ],
            )
        except APITimeoutError as exc:
            raise LLMTimeoutError(
                f"OpenAI request timed out after {self.timeout_seconds}s"
            ) from exc
        except (APIConnectionError, RateLimitError, APIStatusError) as exc:
            raise LLMProviderError(f"OpenAI provider error: {exc}") from exc

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        choice = response.choices[0]
        usage = response.usage

        token_usage = TokenUsage(
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )

        logger.info(
            "openai_completion",
            extra={
                "event": "openai_completion",
                "provider": "openai",
                "model": response.model,
                "latency_ms": latency_ms,
                "status": "ok",
            },
        )
        logger.debug(
            "openai_token_usage",
            extra={
                "event": "openai_token_usage",
                "provider": "openai",
                "model": response.model,
                "tokens": token_usage.total_tokens,
            },
        )

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=token_usage,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, messages: list[Message]) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": message.role.value, "content": message.content}
                    for message in messages
                ],
                stream=True,
            )
        except APITimeoutError as exc:
            raise LLMTimeoutError(
                f"OpenAI stream timed out after {self.timeout_seconds}s"
            ) from exc
        except (APIConnectionError, RateLimitError, APIStatusError) as exc:
            raise LLMProviderError(f"OpenAI provider error: {exc}") from exc

        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
