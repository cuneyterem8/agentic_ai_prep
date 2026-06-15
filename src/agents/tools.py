from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Tool(Protocol):
    name: str
    description: str

    async def run(self, arguments: dict[str, Any]) -> ToolResult: ...


@dataclass
class KnowledgeSearchTool:
    """Low-risk read-only tool — authorization domain katmanında kalır."""

    name: str = "knowledge_search"
    description: str = "Search internal banking knowledge base."

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="query is required",
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Found policy snippets for: {query}",
            metadata={"read_only": True},
        )


@dataclass
class TransferMoneyTool:
    """High-risk tool — policy engine approval olmadan çalışmamalı."""

    name: str = "transfer_money"
    description: str = "Transfer money between accounts."

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        amount = arguments.get("amount")
        destination = str(arguments.get("destination", "")).strip()

        if amount is None or not destination:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="amount and destination are required",
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Transfer scheduled: {amount} TL to {destination}",
            metadata={"irreversible": True},
        )


def get_tool_registry() -> dict[str, KnowledgeSearchTool | TransferMoneyTool]:
    return {
        "knowledge_search": KnowledgeSearchTool(),
        "transfer_money": TransferMoneyTool(),
    }
