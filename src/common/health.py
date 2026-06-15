from src.common.config import Settings, get_settings


def healthcheck(settings: Settings | None = None) -> dict[str, str | bool]:
    cfg = settings or get_settings()
    has_api_key = cfg.openai_api_key is not None and bool(
        cfg.openai_api_key.get_secret_value().strip()
    )

    return {
        "status": "ok",
        "app_name": cfg.app_name,
        "app_version": cfg.app_version,
        "environment": cfg.app_env,
        "llm_provider": cfg.llm_provider,
        "openai_configured": has_api_key,
        "database_url": cfg.database_url.split("://", 1)[0],
    }
