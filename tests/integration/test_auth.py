from __future__ import annotations

from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "Password123!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "dup@example.com",
            "username": "user1",
            "password": "Password123!",
        }
        await client.post("/api/v1/auth/register", json=payload)
        payload["username"] = "user2"
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "someuser",
                "password": "Password123!",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "valid@example.com",
                "username": "validuser",
                "password": "short",
            },
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "Password123!",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "Password123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@example.com",
                "username": "wrongpwuser",
                "password": "Password123!",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "WrongPassword!"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "Password123!"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    async def test_refresh_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "username": "refreshuser",
                "password": "Password123!",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "Password123!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh2@example.com",
                "username": "refreshuser2",
                "password": "Password123!",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh2@example.com", "password": "Password123!"},
        )
        access_token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401


class TestGetMe:
    async def test_get_me_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["username"] == "testuser"

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        client.headers["Authorization"] = "Bearer invalid.token.here"
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
