import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GuardrailCategory(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    TOOL_VALIDATION = "tool_validation"


class InputGuardrailResult(BaseModel):
    allowed: bool
    blocked: bool
    risk_level: str = "low"
    categories: list[GuardrailCategory] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"reveal\s+(the\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?instructions",
    r"you\s+are\s+now\s+(in\s+)?(developer|admin|root)\s+mode",
    r"jailbreak",
    r"\bdan\s+mode\b",
    r"override\s+(safety|security|policy)",
    r"önceki\s+talimatları\s+yok\s+say",
    r"sistem\s+promptunu\s+paylaş",
)

EXFILTRATION_PATTERNS = (
    r"\ball\s+customers\b",
    r"\bother\s+users?\b",
    r"\bdump\s+(the\s+)?database\b",
    r"\bexport\s+all\b",
    r"\bcustomer\s+list\b",
    r"\btüm\s+müşteriler",
    r"\bbaşka\s+kullanıcıların\b",
    r"\bherkesin\s+hesap\b",
    r"\biban\s+listesi\b",
    r"\bpii\b",
)

TOOL_ARGUMENT_SCHEMAS: dict[str, dict[str, Any]] = {
    "knowledge_search": {
        "required": ["query"],
        "max_query_length": 500,
    },
    "transfer_money": {
        "required": ["amount", "destination"],
        "max_amount": 500_000,
        "destination_pattern": r"^TR\d{24}$",
    },
}


def _match_patterns(text: str, patterns: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    for pattern in patterns:
        if re.search(pattern, lowered, re.IGNORECASE):
            hits.append(pattern)
    return hits


def detect_prompt_injection(text: str) -> list[str]:
    return _match_patterns(text, INJECTION_PATTERNS)


def detect_data_exfiltration(text: str) -> list[str]:
    return _match_patterns(text, EXFILTRATION_PATTERNS)


def validate_user_input(text: str) -> InputGuardrailResult:
    """Input katmanı guardrail — prompt injection ve data exfiltration."""
    reasons: list[str] = []
    categories: list[GuardrailCategory] = []

    injection_hits = detect_prompt_injection(text)
    if injection_hits:
        categories.append(GuardrailCategory.PROMPT_INJECTION)
        reasons.append("Prompt injection pattern detected")

    exfiltration_hits = detect_data_exfiltration(text)
    if exfiltration_hits:
        categories.append(GuardrailCategory.DATA_EXFILTRATION)
        reasons.append("Potential data exfiltration request detected")

    if reasons:
        return InputGuardrailResult(
            allowed=False,
            blocked=True,
            risk_level="high",
            categories=categories,
            reasons=reasons,
        )

    return InputGuardrailResult(
        allowed=True,
        blocked=False,
        risk_level="low",
    )


def validate_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> InputGuardrailResult:
    """Tool execution öncesi argüman şema ve limit kontrolü."""
    schema = TOOL_ARGUMENT_SCHEMAS.get(tool_name)
    if schema is None:
        return InputGuardrailResult(
            allowed=False,
            blocked=True,
            risk_level="high",
            categories=[GuardrailCategory.TOOL_VALIDATION],
            reasons=[f"Unknown tool schema: {tool_name}"],
        )

    reasons: list[str] = []

    for field in schema.get("required", []):
        if field not in arguments or arguments[field] in (None, ""):
            reasons.append(f"Missing required tool argument: {field}")

    if tool_name == "knowledge_search":
        query = str(arguments.get("query", ""))
        max_len = schema.get("max_query_length", 500)
        if len(query) > max_len:
            reasons.append(f"Query exceeds max length ({max_len})")

    if tool_name == "transfer_money":
        amount = arguments.get("amount")
        if amount is not None:
            try:
                numeric_amount = float(amount)
            except (TypeError, ValueError):
                reasons.append("Transfer amount must be numeric")
            else:
                if numeric_amount <= 0:
                    reasons.append("Transfer amount must be positive")
                if numeric_amount > schema.get("max_amount", 500_000):
                    reasons.append("Transfer amount exceeds policy limit")

        destination = str(arguments.get("destination", ""))
        pattern = schema.get("destination_pattern")
        if destination and pattern and not re.match(pattern, destination):
            reasons.append("Destination IBAN format is invalid")

    if reasons:
        return InputGuardrailResult(
            allowed=False,
            blocked=True,
            risk_level="high",
            categories=[GuardrailCategory.TOOL_VALIDATION],
            reasons=reasons,
        )

    return InputGuardrailResult(allowed=True, blocked=False, risk_level="low")
