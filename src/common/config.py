from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr | None = None
    llm_provider: Literal["mock", "openai"] = "mock"
    openai_model: str = "gpt-4o"
    openai_fallback_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0
    prompt_version: str = "v1"
    llm_prompt_cost_per_1k_usd: float = 0.005
    llm_completion_cost_per_1k_usd: float = 0.015

    log_level: str = "INFO"
    app_env: Literal["development", "staging", "production"] = "development"
    database_url: str = "sqlite:///./data/app.db"

    app_name: str = Field(default="agenticai-ing-prep")
    app_version: str = Field(default="0.1.0")


@lru_cache
def get_settings() -> Settings:
    return Settings()
