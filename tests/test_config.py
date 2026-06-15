from src.common.config import Settings


def test_settings_defaults_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings(_env_file=None)

    assert settings.llm_provider == "mock"
    assert settings.openai_model == "gpt-4o"
    assert settings.log_level == "INFO"
    assert settings.app_env == "development"


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_ENV", "staging")

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "openai"
    assert settings.log_level == "DEBUG"
    assert settings.app_env == "staging"
