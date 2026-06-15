import json
import re
from enum import Enum
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from src.common.errors import ValidationError

T = TypeVar("T", bound=BaseModel)


class IntentType(str, Enum):
    KNOWLEDGE_QUESTION = "knowledge_question"
    ACCOUNT_ACTION = "account_action"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntentClassification(BaseModel):
    intent: IntentType
    risk_level: RiskLevel
    needs_human_approval: bool = Field(
        description="True when action is risky and requires human approval.",
    )


def extract_json_block(text: str) -> str:
    """Pull JSON object from raw LLM text, including fenced code blocks."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text.strip()


def parse_structured_output(raw_text: str, model: type[T]) -> T:
    """Validate LLM output against a Pydantic schema."""
    candidate = extract_json_block(raw_text)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"LLM output is not valid JSON: {exc}") from exc

    try:
        return model.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(f"LLM output failed schema validation: {exc}") from exc
