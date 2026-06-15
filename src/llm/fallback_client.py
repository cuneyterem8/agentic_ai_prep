import logging

from src.common.errors import LLMProviderError, LLMTimeoutError, TransientError
from src.llm.base import LLMClient, LLMResponse, Message

logger = logging.getLogger("agenticai")


class FallbackLLMClient:
    """Interface-level model fallback — primary fails → secondary devreye girer."""

    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self.primary = primary
        self.fallback = fallback

    async def complete(self, messages: list[Message]) -> LLMResponse:
        try:
            return await self.primary.complete(messages)
        except (LLMProviderError, LLMTimeoutError, TransientError) as exc:
            logger.warning(
                "llm_fallback_triggered",
                extra={
                    "event": "llm_fallback_triggered",
                    "reason": str(exc),
                    "status": "fallback",
                },
            )
            response = await self.fallback.complete(messages)
            return LLMResponse(
                content=response.content,
                model=f"fallback:{response.model}",
                usage=response.usage,
                finish_reason=response.finish_reason,
            )

    async def stream(self, messages: list[Message]):
        try:
            async for token in self.primary.stream(messages):
                yield token
        except (LLMProviderError, LLMTimeoutError, TransientError):
            async for token in self.fallback.stream(messages):
                yield token
