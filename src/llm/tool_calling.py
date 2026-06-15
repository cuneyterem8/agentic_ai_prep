from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field

from src.common.errors import ValidationError


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ParsedToolCalls(BaseModel):
    tool_calls: list[ToolCall] = Field(default_factory=list)
    assistant_content: str | None = None


def parse_tool_calls_payload(payload: dict[str, Any]) -> ParsedToolCalls:
    """Parse OpenAI-style tool call payload from a completion response dict."""
    choices = payload.get("choices") or []
    if not choices:
        return ParsedToolCalls()

    message = choices[0].get("message") or {}
    assistant_content = message.get("content")
    raw_calls = message.get("tool_calls") or []

    tool_calls: list[ToolCall] = []
    for raw in raw_calls:
        function = raw.get("function") or {}
        name = function.get("name")
        if not name:
            continue

        arguments_raw = function.get("arguments", "{}")
        if isinstance(arguments_raw, str):
            import json

            try:
                arguments = json.loads(arguments_raw)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Tool arguments are not valid JSON: {exc}") from exc
        elif isinstance(arguments_raw, dict):
            arguments = arguments_raw
        else:
            raise ValidationError("Tool arguments must be JSON object or string")

        tool_calls.append(
            ToolCall(
                id=str(raw.get("id", "")),
                name=name,
                arguments=arguments,
            )
        )

    return ParsedToolCalls(tool_calls=tool_calls, assistant_content=assistant_content)


def validate_tool_calls(
    parsed: ParsedToolCalls,
    *,
    allowed_tools: set[str],
) -> ParsedToolCalls:
    for call in parsed.tool_calls:
        if call.name not in allowed_tools:
            raise ValidationError(f"Tool '{call.name}' is not allowed")

    return parsed
