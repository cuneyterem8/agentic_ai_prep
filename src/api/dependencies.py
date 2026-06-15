from src.llm.base import LLMClient
from src.llm.factory import create_llm_client


def get_llm_client() -> LLMClient:
    return create_llm_client()
