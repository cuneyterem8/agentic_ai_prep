import uuid

import pytest
from fastapi.testclient import TestClient

from src.agents.workflow import clear_checkpoints
from src.api.main import app
from src.case_study.scenarios import SCENARIOS
from src.data.bootstrap import build_data_stores, get_data_stores
from src.observability.traces import clear_trace_store


@pytest.fixture
def in_memory_stores(monkeypatch, tmp_path):
    db_path = tmp_path / "case_study.db"
    stores = build_data_stores(f"sqlite+pysqlite:///{db_path}")
    get_data_stores.cache_clear()
    monkeypatch.setattr("src.api.routers.workflow.get_data_stores", lambda: stores)
    return stores


@pytest.fixture(autouse=True)
def reset_state():
    clear_checkpoints()
    clear_trace_store()
    yield
    clear_checkpoints()
    clear_trace_store()


@pytest.fixture
def client():
    return TestClient(app)


def _run_workflow(client, message: str, **extra):
    return client.post(
        "/v1/workflow/run",
        json={
            "user_id": "employee-1",
            "conversation_id": f"conv-{uuid.uuid4()}",
            "message": message,
            **extra,
        },
    )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.name for s in SCENARIOS])
def test_case_study_scenario_via_api(client, in_memory_stores, scenario):
    response = _run_workflow(client, scenario.message)
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == scenario.expected_status
    assert body["trace_id"]
    assert body["trace_summary"] is not None

    if scenario.should_block:
        assert body["steps_completed"] == []
        return

    for step in scenario.expected_steps:
        assert step in body["steps_completed"]

    if scenario.requires_approval_resume:
        assert body["needs_human_approval"] is True
        resume = _run_workflow(
            client,
            scenario.message,
            conversation_id=body["conversation_id"],
            run_id=body["run_id"],
            approval_granted=True,
            approval_id=body["approval_id"],
        )
        assert resume.status_code == 200
        resumed = resume.json()
        assert resumed["status"] == "completed"
        assert "execute_tool" in resumed["steps_completed"]
        assert resumed["final_answer"]


def test_case_study_trace_timeline_has_core_spans(client, in_memory_stores):
    response = _run_workflow(client, "50000 TL üzeri işlemler için onay policy nedir?")
    body = response.json()
    timeline = body["trace_summary"]["timeline"]
    span_names = {item["name"] for item in timeline}
    assert "classify_intent" in span_names
    assert "retrieve_context" in span_names


def test_workflow_unknown_balance_question_completes(client, in_memory_stores):
    """Regression: balance-style questions must not 500 when data dir is available."""
    response = _run_workflow(client, "hesabimda ne kadar para var")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("completed", "blocked")
    assert body["final_answer"]
