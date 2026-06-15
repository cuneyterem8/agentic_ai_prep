from collections.abc import AsyncIterator
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: MessageRole
    content: str


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str = "stop"


class LLMClient(Protocol):
    async def complete(self, messages: list[Message]) -> LLMResponse: ...

    async def stream(self, messages: list[Message]) -> AsyncIterator[str]: ...
