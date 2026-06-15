import json

from fastapi.testclient import TestClient

from src.api.main import app
from src.common.config import Settings
from src.common.health import healthcheck
from src.common.logging import StructuredFormatter, set_correlation_id


def test_healthcheck_function_without_api_key():
    settings = Settings(_env_file=None, openai_api_key=None, llm_provider="mock")
    result = healthcheck(settings)

    assert result["status"] == "ok"
    assert result["llm_provider"] == "mock"
    assert result["openai_configured"] is False


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "X-Correlation-ID" in response.headers


def test_correlation_id_in_log_format():
    set_correlation_id("test-correlation-123")
    formatter = StructuredFormatter()
    record = formatter.format(
        type(
            "LogRecord",
            (),
            {
                "levelname": "INFO",
                "name": "test",
                "getMessage": lambda self: "hello",
                "exc_info": None,
            },
        )()
    )
    payload = json.loads(record)
    assert payload["correlation_id"] == "test-correlation-123"
