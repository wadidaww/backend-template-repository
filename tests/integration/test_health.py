from __future__ import annotations

from httpx import AsyncClient


class TestRootHealthCheck:
    async def test_root_health_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "env" in data

    async def test_root_health_env_is_testing(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.json()["env"] == "testing"


class TestV1HealthCheck:
    async def test_v1_health_ok(self, client: AsyncClient):
        response = await client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    async def test_v1_health_no_auth_required(self, client: AsyncClient):
        """Health endpoint must be accessible without authentication."""
        response = await client.get("/api/v1/health/")
        assert response.status_code == 200


class TestSecurityHeaders:
    async def test_security_headers_present(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"

    async def test_request_id_header_present(self, client: AsyncClient):
        response = await client.get("/health")
        assert "x-request-id" in response.headers
