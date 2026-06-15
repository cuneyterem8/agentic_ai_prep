import pytest

from src.common.errors import ValidationError
from src.llm.structured_output import (
    IntentClassification,
    IntentType,
    RiskLevel,
    extract_json_block,
    parse_structured_output,
)


def test_extract_json_block_from_fenced_output():
    raw = 'Here is result:\n```json\n{"intent":"complaint","risk_level":"medium","needs_human_approval":false}\n```'
    extracted = extract_json_block(raw)
    parsed = parse_structured_output(extracted, IntentClassification)

    assert parsed.intent == IntentType.COMPLAINT
    assert parsed.risk_level == RiskLevel.MEDIUM
    assert parsed.needs_human_approval is False


def test_parse_structured_output_rejects_invalid_schema():
    raw = '{"intent":"invalid_intent","risk_level":"low","needs_human_approval":false}'

    with pytest.raises(ValidationError):
        parse_structured_output(raw, IntentClassification)


def test_parse_structured_output_rejects_non_json():
    with pytest.raises(ValidationError):
        parse_structured_output("not-json-at-all", IntentClassification)
