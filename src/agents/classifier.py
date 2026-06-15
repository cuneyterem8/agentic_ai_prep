import logging

from src.agents.callbacks import ChainCallbackHandler, ChainTimer
from src.common.errors import ValidationError
from src.llm.base import LLMClient, Message, MessageRole
from src.llm.structured_output import IntentClassification, IntentType, RiskLevel, parse_structured_output
from src.llm.service import generate_chat_response
from src.security.input_guardrails import validate_user_input
from src.security.pii import mask_pii

logger = logging.getLogger("agenticai")

CLASSIFICATION_SYSTEM_PROMPT = """You are a banking customer message classifier.
Return ONLY valid JSON with this schema:
{
  "intent": "knowledge_question | account_action | complaint | unknown",
  "risk_level": "low | medium | high",
  "needs_human_approval": true
}
Rules:
- account_action with money movement => high risk, needs_human_approval=true
- complaint => at least medium risk
- knowledge_question => low risk unless sensitive account data is involved
"""


def build_classification_messages(customer_message: str) -> list[Message]:
    return [
        Message(role=MessageRole.SYSTEM, content=CLASSIFICATION_SYSTEM_PROMPT),
        Message(
            role=MessageRole.USER,
            content=f"Classify this customer message:\n{customer_message}",
        ),
    ]


def build_repair_messages(raw_output: str) -> list[Message]:
    return [
        Message(
            role=MessageRole.SYSTEM,
            content="Fix the following text into valid JSON for intent classification schema.",
        ),
        Message(role=MessageRole.USER, content=raw_output),
    ]


async def classify_customer_message(
    customer_message: str,
    client: LLMClient,
    *,
    callbacks: ChainCallbackHandler | None = None,
    max_repairs: int = 1,
) -> IntentClassification:
    """Framework-independent chain — LCEL Runnable eşdeğeri."""
    input_guardrail = validate_user_input(customer_message)
    if input_guardrail.blocked:
        logger.warning(
            "input_guardrail_blocked",
            extra={
                "event": "input_guardrail_blocked",
                "message_preview": mask_pii(customer_message[:120]),
                "categories": [item.value for item in input_guardrail.categories],
                "status": "blocked",
            },
        )
        return IntentClassification(
            intent=IntentType.UNKNOWN,
            risk_level=RiskLevel.HIGH,
            needs_human_approval=True,
        )

    handler = callbacks or ChainCallbackHandler()
    timer = ChainTimer()
    chain_name = "classify_customer_message"

    handler.on_chain_start(chain_name, {"customer_message": customer_message})

    messages = build_classification_messages(customer_message)
    response = await generate_chat_response(messages, client, timeout_seconds=15.0)

    handler.on_llm_end(
        chain_name,
        latency_ms=timer.elapsed_ms(),
        model=response.model,
        tokens=response.usage.total_tokens,
    )

    raw_output = response.content
    last_error: ValidationError | None = None

    try:
        parsed = parse_structured_output(raw_output, IntentClassification)
        handler.on_parse_success(chain_name, parsed.model_dump())
        handler.on_chain_end(chain_name, latency_ms=timer.elapsed_ms())
        return parsed
    except ValidationError as exc:
        last_error = exc
        handler.on_parse_error(chain_name, str(exc), raw_output)

    repairs_left = max_repairs
    current_raw = raw_output

    while repairs_left > 0:
        repairs_left -= 1
        repair_response = await generate_chat_response(
            build_repair_messages(current_raw),
            client,
            timeout_seconds=10.0,
            max_attempts=1,
        )
        current_raw = repair_response.content
        try:
            parsed = parse_structured_output(current_raw, IntentClassification)
            handler.on_parse_success(chain_name, parsed.model_dump())
            handler.on_chain_end(chain_name, latency_ms=timer.elapsed_ms())
            return parsed
        except ValidationError as exc:
            last_error = exc
            handler.on_parse_error(chain_name, str(exc), current_raw)

    assert last_error is not None
    raise last_error
