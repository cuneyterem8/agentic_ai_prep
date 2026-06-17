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
    assert body["stage16"]["total_questions"] >= 95
    assert body["overview"]["total_interview_questions"] >= 95


def test_learning_hub_stage4_has_react_content(client):
    response = client.get("/v1/learning-hub/stages/4")
    stage = response.json()["stage"]
    topics = stage.get("topics", [])
    assert "ReAct" in topics
    paths = [c["path"] for c in stage.get("classes", [])]
    assert "src/agents/react_loop.py" in paths


def test_learning_hub_stage6_has_pipeline(client):
    response = client.get("/v1/learning-hub/stages/6")
    stage = response.json()["stage"]
    paths = [c["path"] for c in stage.get("classes", [])]
    assert "src/rag/pipeline.py" in paths
    assert "src/rag/preparation.py" in paths


def test_learning_hub_stage16_master_answer(client):
    response = client.get("/v1/learning-hub/stages/16")
    stage = response.json()["stage"]
    assert stage.get("master_technical_answer")
    assert stage.get("interview_cheatsheet")


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


def test_all_stages_classes_include_implementation_details():
    hub = build_hub_content()
    for stage in hub["stages"]:
        for cls in stage.get("classes", []):
            assert cls.get("symbols_detail"), (
                f"Stage {stage['id']} class {cls['path']} missing symbols_detail"
            )
            for detail in cls["symbols_detail"]:
                assert detail["code"], f"Missing code for {detail['name']}"
                assert detail["usage"], f"Missing usage for {detail['name']}"


def test_all_stages_include_concept_guide():
    hub = build_hub_content()
    for stage in hub["stages"]:
        guide = stage.get("concept_guide")
        assert guide, f"Stage {stage['id']} missing concept_guide"
        for key in ("title", "definition", "purpose", "how_it_works", "core_logic", "in_this_project"):
            assert guide.get(key), f"Stage {stage['id']} concept_guide missing {key}"


def test_interview_qa_answers_are_expanded():
    hub = build_hub_content()
    min_answer_len = 120
    min_deep_dive_len = 80
    for stage in hub["stages"]:
        for qa in stage.get("interview_qa", []):
            assert len(qa.get("answer", "")) >= min_answer_len, (
                f"Stage {stage['id']} Q&A answer too short: {qa.get('question', '')[:50]}"
            )
            if qa.get("deep_dive"):
                assert len(qa["deep_dive"]) >= min_deep_dive_len, (
                    f"Stage {stage['id']} deep_dive too short"
                )
    for qa in hub["stage15"].get("interview_qa", []):
        assert len(qa.get("answer", "")) >= min_answer_len


def test_ui_hub_assets_are_served(client):
    for asset in ("styles.css", "hub.js", "demo.js", "playground.js"):
        response = client.get(f"/ui/{asset}")
        assert response.status_code == 200


def test_ui_index_loads_hub(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Agentic AI Prep" in response.text
    assert "hub.js" in response.text
