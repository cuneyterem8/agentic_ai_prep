import asyncio
import json
from collections.abc import AsyncIterator

from src.llm.base import LLMResponse, Message, MessageRole, TokenUsage


class MockLLMClient:
    """Deterministic LLM adapter for offline tests and local development."""

    def __init__(
        self,
        *,
        model: str = "mock-gpt",
        default_response: str = "Mock response: request received.",
    ) -> None:
        self.model = model
        self.default_response = default_response

    async def complete(self, messages: list[Message]) -> LLMResponse:
        if _is_classification_prompt(messages):
            content = _mock_classification(messages)
        elif _is_repair_prompt(messages):
            content = _mock_repair(messages)
        elif _is_sql_analyst_prompt(messages):
            content = _mock_sql_generation(messages)
        elif _is_sql_regeneration_prompt(messages):
            content = _mock_sql_regeneration(messages)
        else:
            content = self._default_content(messages)

        prompt_tokens = sum(len(m.content.split()) for m in messages)

        return LLMResponse(
            content=content,
            model=self.model,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=len(content.split()),
            ),
            finish_reason="stop",
        )

    def _default_content(self, messages: list[Message]) -> str:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == MessageRole.USER),
            None,
        )

        if last_user and last_user.strip().lower().startswith("echo:"):
            return last_user.split(":", 1)[1].strip()
        if last_user:
            return f"{self.default_response} Last user message: {last_user}"
        return self.default_response

    async def stream(self, messages: list[Message]) -> AsyncIterator[str]:
        response = await self.complete(messages)
        for token in response.content.split():
            yield token + " "
            await asyncio.sleep(0.01)


def _is_classification_prompt(messages: list[Message]) -> bool:
    return any(
        m.role == MessageRole.SYSTEM and "customer message classifier" in m.content.lower()
        for m in messages
    )


def _is_repair_prompt(messages: list[Message]) -> bool:
    return any(
        m.role == MessageRole.SYSTEM and "fix the following text" in m.content.lower()
        for m in messages
    )


def _extract_customer_message(user_content: str) -> str:
    marker = "classify this customer message:"
    if marker in user_content.lower():
        return user_content.split(":", 1)[-1].strip()
    return user_content


def _mock_classification(messages: list[Message]) -> str:
    last_user = next(
        (m.content for m in reversed(messages) if m.role == MessageRole.USER),
        "",
    )
    text = _extract_customer_message(last_user).lower()

    if any(word in text for word in ("şikayet", "complaint", "memnun değil")):
        payload = {
            "intent": "complaint",
            "risk_level": "medium",
            "needs_human_approval": False,
        }
    elif any(word in text for word in ("transfer", "para gönder", "hesaptan", "hesabımdan", "para çek", "withdraw")):
        payload = {
            "intent": "account_action",
            "risk_level": "high",
            "needs_human_approval": True,
        }
    elif any(word in text for word in ("nedir", "nasıl", "policy", "limit")):
        payload = {
            "intent": "knowledge_question",
            "risk_level": "low",
            "needs_human_approval": False,
        }
    else:
        payload = {
            "intent": "unknown",
            "risk_level": "low",
            "needs_human_approval": False,
        }

    return json.dumps(payload)


def _mock_repair(messages: list[Message]) -> str:
    return json.dumps(
        {
            "intent": "complaint",
            "risk_level": "medium",
            "needs_human_approval": False,
        }
    )


def _is_sql_analyst_prompt(messages: list[Message]) -> bool:
    return any(
        m.role == MessageRole.SYSTEM and "read-only sql analyst" in m.content.lower()
        for m in messages
    )


def _mock_sql_generation(messages: list[Message]) -> str:
    last_user = next(
        (m.content for m in reversed(messages) if m.role == MessageRole.USER),
        "",
    )
    tenant_id = "tenant-a"
    question = last_user

    if "Tenant:" in last_user:
        parts = last_user.split("Question:", 1)
        question = parts[1].split("Return SQL only.", 1)[0].strip() if len(parts) > 1 else last_user
        tenant_id = parts[0].split("Tenant:", 1)[-1].strip()

    lowered = question.lower()
    if "drop" in lowered:
        return "DROP TABLE transactions"
    if "delete" in lowered:
        return f"DELETE FROM transactions WHERE tenant_id = '{tenant_id}'"
    if "total" in lowered or "sum" in lowered:
        return (
            f"SELECT SUM(amount) AS total_amount FROM transactions "
            f"WHERE tenant_id = '{tenant_id}' LIMIT 100"
        )
    if "join" in lowered:
        return (
            "SELECT t1.id, t2.id FROM transactions t1 "
            "JOIN transactions t2 ON t1.customer_id = t2.customer_id "
            f"WHERE t1.tenant_id = '{tenant_id}' LIMIT 10"
        )
    return (
        f"SELECT id, customer_id, amount, category FROM transactions "
        f"WHERE tenant_id = '{tenant_id}' LIMIT 20"
    )


def _is_sql_regeneration_prompt(messages: list[Message]) -> bool:
    return any(
        m.role == MessageRole.SYSTEM
        and (
            "regenerate sql" in m.content.lower()
            or "fix sql" in m.content.lower()
        )
        for m in messages
    )


def _extract_sql_prompt_context(last_user: str) -> tuple[str, str]:
    tenant_id = "tenant-a"
    question = last_user

    if "Tenant:" in last_user and "Question:" in last_user:
        tenant_id = last_user.split("Tenant:", 1)[1].split("Question:", 1)[0].strip()
        question = last_user.split("Question:", 1)[1]
        for marker in ("Rejected SQL:", "Bad SQL:", "Return corrected SELECT SQL only."):
            question = question.split(marker, 1)[0]
        question = question.strip()

    return tenant_id, question


def _build_safe_select_sql(question: str, tenant_id: str) -> str:
    lowered = question.lower()
    if "total" in lowered or "sum" in lowered:
        return (
            f"SELECT SUM(amount) AS total_amount FROM transactions "
            f"WHERE tenant_id = '{tenant_id}' LIMIT 100"
        )
    if "join" in lowered:
        return (
            "SELECT t1.id, t2.id FROM transactions t1 "
            "JOIN transactions t2 ON t1.customer_id = t2.customer_id "
            f"WHERE t1.tenant_id = '{tenant_id}' LIMIT 10"
        )
    return (
        f"SELECT id, customer_id, amount, category FROM transactions "
        f"WHERE tenant_id = '{tenant_id}' LIMIT 20"
    )


def _mock_sql_regeneration(messages: list[Message]) -> str:
    last_user = next(
        (m.content for m in reversed(messages) if m.role == MessageRole.USER),
        "",
    )
    tenant_id, question = _extract_sql_prompt_context(last_user)
    return _build_safe_select_sql(question, tenant_id)
