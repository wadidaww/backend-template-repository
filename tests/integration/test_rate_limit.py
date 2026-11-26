from __future__ import annotations

from collections.abc import Iterator

import pytest
from httpx import AsyncClient

from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_limiter() -> Iterator[None]:
    limiter.reset()
    yield
    limiter.reset()


class TestAuthRateLimit:
    async def test_login_is_limited(self, client: AsyncClient) -> None:
        body = {"email": "nobody@example.com", "password": "wrong-password"}
        statuses = [
            (await client.post("/api/v1/auth/login", json=body)).status_code
            for _ in range(11)
        ]
        assert statuses[:10] == [401] * 10
        assert statuses[10] == 429

    async def test_limit_headers_present(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "password": "Password123!",
            },
        )
        assert response.status_code == 201
        assert response.headers["x-ratelimit-limit"] == "10"

    async def test_429_has_retry_after(self, client: AsyncClient) -> None:
        body = {"email": "nobody@example.com", "password": "wrong-password"}
        for _ in range(11):
            response = await client.post("/api/v1/auth/login", json=body)
        assert response.status_code == 429
        assert "retry-after" in response.headers

    async def test_health_is_exempt(self, client: AsyncClient) -> None:
        for _ in range(30):
            response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
