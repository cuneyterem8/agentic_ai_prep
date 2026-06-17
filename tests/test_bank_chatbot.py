import pytest

from src.case_study.bank_chatbot import BankChatbotSession, bank_chatbot
from src.llm.mock_client import MockLLMClient


@pytest.mark.asyncio
async def test_bank_chatbot_faq_uses_rag():
    result = await bank_chatbot(
        user_id="user-1",
        query="Şifre sıfırlama policy nedir?",
        session=BankChatbotSession(),
        client=MockLLMClient(),
    )
    assert result.intent in ("general_faq", "complaint", "unknown")
    assert result.answer


@pytest.mark.asyncio
async def test_bank_chatbot_balance_requires_auth():
    result = await bank_chatbot(
        user_id="user-1",
        query="Bakiyem ne kadar?",
        session=BankChatbotSession(authenticated=False),
        client=MockLLMClient(),
    )
    assert "giriş" in result.answer.lower()


@pytest.mark.asyncio
async def test_bank_chatbot_balance_with_auth():
    result = await bank_chatbot(
        user_id="user-1",
        query="Bakiyem ne kadar?",
        session=BankChatbotSession(authenticated=True),
        client=MockLLMClient(),
    )
    assert "bakiye" in result.answer.lower() or "TL" in result.answer
