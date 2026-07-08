from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz_returns_uniform_response():
    client = TestClient(create_app())

    response = client.get("/api/v1/healthz", headers={"X-Trace-Id": "test-trace"})

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "test-trace"
    assert response.json() == {
        "success": True,
        "data": {"status": "ok", "service": "course-agent-backend"},
        "error": None,
        "trace_id": "test-trace",
    }

