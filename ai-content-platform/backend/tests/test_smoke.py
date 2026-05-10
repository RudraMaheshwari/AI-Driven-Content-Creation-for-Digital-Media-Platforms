"""Minimal smoke test — boots the FastAPI app in mock mode and hits /health."""
from __future__ import annotations

import os

# Force mock mode so this test never tries to call Gemini.
os.environ.setdefault("CONTENT_MOCK", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./storage/content_test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402


def test_health_ok() -> None:
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["mock_mode"] is True


def test_generate_mock_path() -> None:
    with TestClient(app) as client:
        r = client.post(
            "/generate",
            json={
                "prompt": "Write a launch tweet for a new espresso bar",
                "content_type": "social_post",
                "platform": "twitter",
                "tone": "witty",
                "length": "short",
            },
        )
        assert r.status_code == 202
        record_id = r.json()["id"]
        assert record_id

        # Background task should run on the testclient threadpool; poll briefly.
        for _ in range(20):
            poll = client.get(f"/generate/{record_id}").json()
            if poll["status"] in {"completed", "failed"}:
                break
        assert poll["status"] == "completed"
        assert poll["final_output"]
