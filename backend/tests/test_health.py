from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "procureflow-api"}


def test_unknown_route():
    with TestClient(app) as client:
        response = client.get("/api/unknown")

    assert response.status_code == 404
