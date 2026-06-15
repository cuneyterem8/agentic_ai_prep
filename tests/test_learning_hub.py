import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.learning_hub.build import build_hub_content


@pytest.fixture
def client():
    return TestClient(app)


def test_learning_hub_endpoint_returns_full_content(client):
    response = client.get("/v1/learning-hub")
    assert response.status_code == 200
    body = response.json()
    assert body["version"]
    assert len(body["stages"]) == 15
    assert body["stage15"]["stories"]
    assert body["stage16"]["total_questions"] >= 70
    assert body["overview"]["total_interview_questions"] >= 70


def test_learning_hub_stage_endpoint(client):
    response = client.get("/v1/learning-hub/stages/4")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "technical"
    assert body["stage"]["id"] == 4
    assert body["stage"]["classes"]


def test_learning_hub_stage15_leadership(client):
    response = client.get("/v1/learning-hub/stages/15")
    body = response.json()
    assert body["type"] == "leadership"
    assert len(body["stage"]["stories"]) == 5
    assert len(body["stage"]["interview_qa"]) == 5


def test_learning_hub_stage16_simulation(client):
    response = client.get("/v1/learning-hub/stages/16")
    body = response.json()
    assert body["type"] == "simulation"
    assert body["stage"]["simulation_schedule"]
    assert len(body["stage"]["all_interview_qa"]) == body["stage"]["total_questions"]


def test_build_hub_content_has_interview_qa_per_stage():
    hub = build_hub_content()
    for stage in hub["stages"]:
        assert len(stage.get("interview_qa", [])) >= 3, f"Stage {stage['id']} missing Q&A"
        assert len(stage.get("classes", [])) >= 1, f"Stage {stage['id']} missing classes"


def test_ui_hub_assets_are_served(client):
    for asset in ("styles.css", "hub.js", "demo.js", "playground.js"):
        response = client.get(f"/ui/{asset}")
        assert response.status_code == 200


def test_ui_index_loads_hub(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Agentic AI Prep" in response.text
    assert "hub.js" in response.text
