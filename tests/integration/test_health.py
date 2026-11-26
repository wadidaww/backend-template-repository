from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.modules.health import router as health_router


async def _ok() -> None:
    return None


async def _fail() -> None:
    raise ConnectionError("down")


class TestLiveness:
    async def test_live_ok(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["env"] == "testing"
        assert "version" in data

    async def test_live_no_auth_required(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200


class TestReadiness:
    async def test_ready_when_all_checks_pass(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(health_router, "CHECKS", {"database": _ok, "redis": _ok})
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "checks": {"database": "ok", "redis": "ok"},
        }

    async def test_not_ready_when_a_check_fails(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(health_router, "CHECKS", {"database": _ok, "redis": _fail})
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert response.json()["checks"] == {"database": "ok", "redis": "error"}


class TestSecurityHeaders:
    async def test_security_headers_present(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") is not None

    async def test_request_id_generated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert len(response.headers["x-request-id"]) == 32

    async def test_safe_incoming_request_id_is_reused(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/health/live", headers={"X-Request-ID": "abc-123"}
        )
        assert response.headers["x-request-id"] == "abc-123"

    async def test_unsafe_incoming_request_id_is_replaced(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/health/live", headers={"X-Request-ID": "bad id\twith spaces"}
        )
        assert response.headers["x-request-id"] != "bad id\twith spaces"
