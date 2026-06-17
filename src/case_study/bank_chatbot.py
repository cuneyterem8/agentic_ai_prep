"""Deterministic bank chatbot orchestrator — intent routing + policy + RAG/tools."""

from dataclasses import dataclass, field
from typing import Any

from src.agents.classifier import classify_customer_message
from src.llm.base import LLMClient
from src.rag.service import answer_with_sources
from src.security.input_guardrails import validate_user_input


@dataclass
class BankChatbotSession:
    authenticated: bool = False
    mfa_verified: bool = False


@dataclass
class BankChatbotResult:
    intent: str
    answer: str
    escalated: bool = False
    audit: dict[str, Any] = field(default_factory=dict)


INTENT_MAP = {
    "knowledge_question": "general_faq",
    "account_action": "balance_query",
    "complaint": "complaint",
    "unknown": "unknown",
}


def _map_intent(classification_intent: str, message: str) -> str:
    lower = message.lower()
    if any(w in lower for w in ("fraud", "izinsiz", "şüpheli", "calindi", "çalındı")):
        return "fraud_report"
    if any(w in lower for w in ("transfer", "gönder", "gonder")):
        return "money_transfer"
    if any(w in lower for w in ("bakiye", "balance", "ne kadar para")):
        return "balance_query"
    if any(w in lower for w in ("işlem", "transaction", "son 5")):
        return "transaction_history"
    return INTENT_MAP.get(classification_intent, "unknown")


def authorize_action(session: BankChatbotSession, action: str) -> bool:
    if action in ("balance_query", "transaction_history", "money_transfer"):
        return session.authenticated
    if action == "money_transfer":
        return session.authenticated and session.mfa_verified
    if action == "get_other_customer_info":
        return False
    return True


def apply_output_guardrails(answer: str) -> str:
    lower = answer.lower()
    if any(term in lower for term in ("yatırım tavsiyesi", "hisse al")):
        return "Bu konuda kişisel yatırım tavsiyesi veremem."
    return answer


async def bank_chatbot(
    *,
    user_id: str,
    query: str,
    session: BankChatbotSession,
    client: LLMClient,
) -> BankChatbotResult:
    """Route bank queries: guardrails → intent → policy → RAG or secure response."""
    guardrail = validate_user_input(query)
    if guardrail.blocked:
        return BankChatbotResult(
            intent="blocked",
            answer="Bu isteği güvenli şekilde işleyemiyorum.",
            audit={"blocked": True, "reasons": guardrail.reasons},
        )

    classification = await classify_customer_message(query, client)
    intent = _map_intent(classification.intent.value, query)

    if intent in ("balance_query", "transaction_history", "money_transfer"):
        if not authorize_action(session, intent):
            return BankChatbotResult(
                intent=intent,
                answer="Bu işlem için giriş yapmanız gerekiyor.",
                audit={"user_id": user_id, "auth_required": True},
            )

    if intent in ("general_faq", "complaint"):
        rag = await answer_with_sources(query, client, top_k=3)
        answer = apply_output_guardrails(rag.answer)
        return BankChatbotResult(
            intent=intent,
            answer=answer,
            audit={
                "user_id": user_id,
                "retrieved_doc_ids": rag.source_chunk_ids,
                "intent": intent,
            },
        )

    if intent == "balance_query":
        return BankChatbotResult(
            intent=intent,
            answer="Güncel bakiyeniz: 12.450,00 TL (mock API)",
            audit={"user_id": user_id, "tool": "get_balance"},
        )

    if intent == "transaction_history":
        return BankChatbotResult(
            intent=intent,
            answer="Son 5 işlem: -500 TL EFT, +2000 TL maaş, -120 TL POS (mock API)",
            audit={"user_id": user_id, "tool": "get_recent_transactions"},
        )

    if intent == "money_transfer":
        return BankChatbotResult(
            intent=intent,
            answer=(
                "Transfer talebiniz alındı. Lütfen mobil doğrulamayı tamamlayın. "
                "Para transferi MFA onayı olmadan gerçekleştirilmez."
            ),
            audit={"user_id": user_id, "mfa_required": True},
        )

    if intent == "fraud_report":
        return BankChatbotResult(
            intent=intent,
            answer="Şüpheli işlem bildiriminiz alınmıştır. Kayıt numaranız: FRAUD-2025-001.",
            audit={"user_id": user_id, "case_id": "FRAUD-2025-001"},
        )

    return BankChatbotResult(
        intent=intent,
        answer="Talebiniz canlı temsilciye aktarılıyor.",
        escalated=True,
        audit={"user_id": user_id, "escalated": True},
    )
