import json

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.evals import feedback_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def feedback_file(tmp_path, monkeypatch):
    path = tmp_path / "feedback.jsonl"
    monkeypatch.setattr(feedback_store, "FEEDBACK_PATH", path)
    return path


def test_submit_feedback_persists_record(client, feedback_file):
    response = client.post(
        "/v1/feedback",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "rating": "positive",
            "trace_id": "trace-abc",
            "run_id": "run-xyz",
            "message_preview": "Şifre sıfırlama policy nedir?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == "positive"
    assert body["trace_id"] == "trace-abc"
    assert body["run_id"] == "run-xyz"
    assert body["feedback_id"]

    lines = feedback_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["user_id"] == "user-1"


def test_submit_feedback_masks_pii_in_preview(client, feedback_file):
    response = client.post(
        "/v1/feedback",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "rating": "negative",
            "message_preview": "Transfer için IBAN TR123456789012345678901234",
        },
    )

    assert response.status_code == 200
    preview = response.json()["message_preview"]
    assert "TR123456789012345678901234" not in preview
    assert "[IBAN_REDACTED]" in preview


def test_list_recent_feedback_returns_newest_first(client, feedback_file):
    for rating in ("positive", "negative"):
        client.post(
            "/v1/feedback",
            json={
                "user_id": "user-1",
                "conversation_id": "conv-1",
                "rating": rating,
            },
        )

    response = client.get("/v1/feedback/recent?limit=1")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["rating"] == "negative"


def test_feedback_invalid_rating_returns_422(client):
    response = client.post(
        "/v1/feedback",
        json={
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "rating": "maybe",
        },
    )
    assert response.status_code == 422


def test_root_redirects_to_ui(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/ui/"


def test_ui_index_is_served(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Agentic AI Prep" in response.text


def test_ui_static_assets_are_served(client):
    for asset in ("styles.css", "hub.js", "demo.js", "playground.js", "app.js"):
        response = client.get(f"/ui/{asset}")
        assert response.status_code == 200
