"""Tests for private (authenticated) endpoints."""
from fastapi.testclient import TestClient

from tests.conftest import TEST_SUB, make_token


def test_private_no_token(client: TestClient) -> None:
    """Requests without a token should be rejected with 403."""
    response = client.get("/api/private")
    assert response.status_code == 403


def test_private_invalid_token(client: TestClient) -> None:
    """A malformed token should return 401."""
    response = client.get("/api/private", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_private_valid_token(client: TestClient) -> None:
    """A properly signed token should grant access."""
    token = make_token()
    response = client.get("/api/private", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["sub"] == TEST_SUB
    assert "message" in data


def test_private_wrong_audience(client: TestClient) -> None:
    """Token with wrong audience should be rejected."""
    token = make_token(audience="https://wrong-api/")
    response = client.get("/api/private", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_private_wrong_issuer(client: TestClient) -> None:
    """Token with wrong issuer should be rejected."""
    token = make_token(issuer="https://evil.auth0.com/")
    response = client.get("/api/private", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
