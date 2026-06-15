import pytest
from fastapi.testclient import TestClient

from src.agents.workflow import CustomerSupportWorkflow, clear_checkpoints
from src.api.main import app
from src.data.bootstrap import build_data_stores, get_data_stores
from src.llm.mock_client import MockLLMClient
from src.observability.metrics import get_metrics
from src.observability.traces import clear_trace_store, start_trace
from src.llm.base import Message, MessageRole
from src.llm.service import generate_chat_response


@pytest.fixture
def in_memory_stores(monkeypatch, tmp_path):
    db_path = tmp_path / "workflow_test.db"
    stores = build_data_stores(f"sqlite+pysqlite:///{db_path}")
    get_data_stores.cache_clear()
    monkeypatch.setattr("src.api.routers.workflow.get_data_stores", lambda: stores)
    return stores


@pytest.fixture(autouse=True)
def reset_observability_state():
    get_metrics().reset()
    clear_trace_store()
    clear_checkpoints()
    yield
    get_metrics().reset()
    clear_trace_store()
    clear_checkpoints()


def test_trace_session_records_span_latencies():
    trace = start_trace(run_id="run-1", prompt_version="v1-test")
    with trace.span("classify_intent", "classification"):
        pass
    with trace.span("retrieve_context", "retrieval"):
        pass

    summary = trace.finish(status="completed")
    trace.close()

    assert summary.trace_id
    assert summary.run_id == "run-1"
    assert summary.prompt_version == "v1-test"
    assert len(summary.timeline) == 2
    assert summary.timeline[0]["name"] == "classify_intent"
    assert summary.timeline[0]["latency_ms"] >= 0


def test_metrics_collector_records_llm_and_http_metrics():
    metrics = get_metrics()
    metrics.record_llm_call(
        model="mock-gpt",
        latency_ms=120.5,
        prompt_tokens=10,
        completion_tokens=20,
        retry_count=1,
        status="ok",
    )
    metrics.record_http_request(
        route="/v1/workflow/run",
        method="POST",
        status_code=200,
        latency_ms=250.0,
    )

    snapshot = metrics.snapshot()
    assert snapshot["counters"]["llm_calls_total"] == 1
    assert snapshot["counters"]["http_requests_total"] == 1
    assert snapshot["counters"]["llm_prompt_tokens_total"] == 10
    assert snapshot["gauges"]["llm_estimated_cost_usd_total"] > 0


@pytest.mark.asyncio
async def test_llm_service_records_trace_span():
    trace = start_trace(run_id="run-llm")
    client = MockLLMClient()

    await generate_chat_response(
        [Message(role=MessageRole.USER, content="echo: hello")],
        client,
        timeout_seconds=5.0,
        max_attempts=1,
    )

    summary = trace.finish(status="completed")
    trace.close()

    llm_spans = [item for item in summary.timeline if item["kind"] == "llm"]
    assert len(llm_spans) == 1
    assert llm_spans[0]["model"] == "mock-gpt"
    assert summary.total_tokens > 0
    assert get_metrics().snapshot()["counters"]["llm_calls_total"] == 1


@pytest.mark.asyncio
async def test_workflow_produces_trace_summary_timeline():
    workflow = CustomerSupportWorkflow(MockLLMClient())
    result = await workflow.run(
        user_id="user-1",
        conversation_id="conv-obs-1",
        customer_message="Şifre sıfırlama policy nedir?",
    )

    assert result.trace_summary is not None
    assert result.trace_id == result.trace_summary.trace_id
    assert result.trace_summary.status == "completed"
    assert result.trace_summary.llm_calls >= 1

    timeline_kinds = {item["kind"] for item in result.trace_summary.timeline}
    assert "classification" in timeline_kinds
    assert "retrieval" in timeline_kinds
    assert "llm" in timeline_kinds
    assert result.trace_summary.total_latency_ms > 0


def test_observability_api_endpoints():
    client = TestClient(app)

    metrics_response = client.get("/v1/observability/metrics")
    assert metrics_response.status_code == 200
    body = metrics_response.json()
    assert "counters" in body
    assert "latencies" in body
    assert "gauges" in body

    missing_trace = client.get("/v1/observability/traces/does-not-exist")
    assert missing_trace.status_code == 404


def test_workflow_api_returns_trace_summary(in_memory_stores):
    client = TestClient(app)
    response = client.post(
        "/v1/workflow/run",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-obs-api",
            "message": "Şifre sıfırlama policy nedir?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"]
    assert body["trace_summary"]["status"] == "completed"
    assert body["trace_summary"]["timeline"]

    trace_response = client.get(f"/v1/observability/traces/{body['trace_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()["run_id"] == body["run_id"]
