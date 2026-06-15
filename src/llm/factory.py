from src.common.config import Settings, get_settings
from src.llm.base import LLMClient
from src.llm.fallback_client import FallbackLLMClient
from src.llm.mock_client import MockLLMClient
from src.llm.openai_client import OpenAIClient


def _has_openai_api_key(settings: Settings) -> bool:
    return settings.openai_api_key is not None and bool(
        settings.openai_api_key.get_secret_value().strip()
    )


def create_llm_client(settings: Settings | None = None) -> LLMClient:
    """Dependency injection factory — mock offline, OpenAI when configured."""
    cfg = settings or get_settings()

    if cfg.llm_provider == "openai" and _has_openai_api_key(cfg):
        api_key = cfg.openai_api_key.get_secret_value()
        primary = OpenAIClient(
            api_key=api_key,
            model=cfg.openai_model,
            timeout_seconds=cfg.llm_timeout_seconds,
        )
        fallback = OpenAIClient(
            api_key=api_key,
            model=cfg.openai_fallback_model,
            timeout_seconds=cfg.llm_timeout_seconds,
        )
        return FallbackLLMClient(primary=primary, fallback=fallback)

    return MockLLMClient(model=f"mock-{cfg.openai_model}")
