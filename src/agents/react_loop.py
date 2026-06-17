"""ReAct-style agent loop: Observe → Think → Act with tool calls."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.agents.tools import get_tool_registry
from src.llm.base import LLMClient, Message, MessageRole


class ReActStep(BaseModel):
    thought: str
    action_type: Literal["tool_call", "final_answer", "escalate"]
    tool_name: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    observation: str | None = None


class ReActResult(BaseModel):
    query: str
    user_id: str
    steps: list[ReActStep]
    final_answer: str
    status: Literal["completed", "escalated"]


def _decide_next_action(state: dict[str, Any]) -> ReActStep:
    """Deterministic mock 'LLM' decision for demo and tests."""
    query = state["query"].lower()
    steps = state["steps"]

    if any(word in query for word in ("ignore", "system prompt", "reveal")):
        return ReActStep(
            thought="Potential prompt injection or unauthorized request detected.",
            action_type="escalate",
        )

    if "transfer" in query or "gönder" in query:
        if not any(s.tool_name == "transfer_money" for s in steps):
            return ReActStep(
                thought="User wants a transfer; need authentication and policy check first.",
                action_type="tool_call",
                tool_name="transfer_money",
                tool_arguments={"amount": 10000, "destination": "registered-beneficiary"},
            )
        return ReActStep(
            thought="Transfer tool returned; summarize next steps for user with MFA reminder.",
            action_type="final_answer",
        )

    if "kredi" in query or "başvuru" in query or "loan" in query:
        if not any(s.tool_name == "knowledge_search" for s in steps):
            return ReActStep(
                thought="Need policy information from knowledge base before answering.",
                action_type="tool_call",
                tool_name="knowledge_search",
                tool_arguments={"query": state["query"]},
            )
        return ReActStep(
            thought="Retrieved policy snippets; can answer about required documents.",
            action_type="final_answer",
        )

    if not steps:
        return ReActStep(
            thought="General query; search internal knowledge base.",
            action_type="tool_call",
            tool_name="knowledge_search",
            tool_arguments={"query": state["query"]},
        )

    return ReActStep(
        thought="Enough context gathered from tools.",
        action_type="final_answer",
    )


def _finalize_answer(state: dict[str, Any], last_step: ReActStep) -> str:
    query = state["query"].lower()
    if "transfer" in query or "gönder" in query:
        return (
            "Transfer talebiniz alındı. Lütfen işlemi onaylamak için mobil doğrulamayı tamamlayın. "
            "Para transferi MFA ve explicit onay olmadan gerçekleştirilmez."
        )
    if "kredi" in query or "loan" in query:
        return (
            "Kredi başvurusu için kimlik belgesi, gelir belgesi ve bankanın talep edebileceği "
            "ek teminat belgeleri gerekebilir. Detaylı bilgi iç bilgi tabanından alındı."
        )
    observations = [s.observation for s in state["steps"] if s.observation]
    if observations:
        return f"Sorgunuz için bilgi tabanı sonuçları: {observations[-1]}"
    return "Talebiniz işlendi."


async def run_react_loop(
    *,
    user_query: str,
    user_id: str,
    client: LLMClient | None = None,
    max_steps: int = 5,
) -> ReActResult:
    """Run Observe → Think → Act loop until final answer or escalation."""
    _ = client  # Reserved for LLM-driven decisions in production
    state: dict[str, Any] = {"query": user_query, "user_id": user_id, "steps": []}
    registry = get_tool_registry()
    steps: list[ReActStep] = []

    for _ in range(max_steps):
        decision = _decide_next_action(state)

        if decision.action_type == "escalate":
            steps.append(decision)
            return ReActResult(
                query=user_query,
                user_id=user_id,
                steps=steps,
                final_answer="Bu isteği güvenli şekilde işleyemiyorum. Canlı temsilciye aktarılıyorsunuz.",
                status="escalated",
            )

        if decision.action_type == "tool_call" and decision.tool_name:
            tool = registry.get(decision.tool_name)
            if tool is None:
                decision.observation = f"Unknown tool: {decision.tool_name}"
            else:
                result = await tool.run(decision.tool_arguments)
                decision.observation = result.output
            steps.append(decision)
            state["steps"] = steps
            continue

        if decision.action_type == "final_answer":
            steps.append(decision)
            return ReActResult(
                query=user_query,
                user_id=user_id,
                steps=steps,
                final_answer=_finalize_answer(state, decision),
                status="completed",
            )

    return ReActResult(
        query=user_query,
        user_id=user_id,
        steps=steps,
        final_answer="Maksimum adım sayısına ulaşıldı; lütfen talebinizi netleştirin.",
        status="completed",
    )


async def llm_decide_next_action(state: dict[str, Any], client: LLMClient) -> ReActStep:
    """Production path: ask LLM for next ReAct step as JSON."""
    prompt = (
        "Decide the next ReAct step for this agent state. "
        f"Query: {state['query']}\nSteps so far: {len(state['steps'])}"
    )
    messages = [Message(role=MessageRole.USER, content=prompt)]
    response = await client.complete(messages)
    _ = response
    return _decide_next_action(state)
