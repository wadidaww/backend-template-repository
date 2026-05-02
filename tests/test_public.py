"""Tests for public (unauthenticated) endpoints."""
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_endpoint(client: TestClient) -> None:
    response = client.get("/api/public")
    assert response.status_code == 200
    assert "message" in response.json()
