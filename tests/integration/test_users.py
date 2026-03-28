from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestListUsers:
    async def test_list_users_as_superuser(
        self,
        superuser_client: AsyncClient,
        test_user: User,
    ):
        response = await superuser_client.get("/api/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    async def test_list_users_as_regular_user_forbidden(
        self, authenticated_client: AsyncClient
    ):
        response = await authenticated_client.get("/api/v1/users/")
        assert response.status_code == 403

    async def test_list_users_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/users/")
        assert response.status_code == 401


class TestGetCurrentUserProfile:
    async def test_get_own_profile(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestGetUser:
    async def test_superuser_can_get_any_user(
        self,
        superuser_client: AsyncClient,
        test_user: User,
    ):
        response = await superuser_client.get(f"/api/v1/users/{test_user.id}")
        assert response.status_code == 200
        assert response.json()["id"] == test_user.id

    async def test_regular_user_cannot_get_other_user(
        self,
        authenticated_client: AsyncClient,
        superuser: User,
    ):
        response = await authenticated_client.get(f"/api/v1/users/{superuser.id}")
        assert response.status_code == 403

    async def test_get_nonexistent_user(self, superuser_client: AsyncClient):
        response = await superuser_client.get("/api/v1/users/nonexistent-id")
        assert response.status_code == 404


class TestUpdateUser:
    async def test_user_can_update_self(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
    ):
        response = await authenticated_client.patch(
            f"/api/v1/users/{test_user.id}",
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_superuser_can_update_any_user(
        self,
        superuser_client: AsyncClient,
        test_user: User,
    ):
        response = await superuser_client.patch(
            f"/api/v1/users/{test_user.id}",
            json={"full_name": "Admin Updated"},
        )
        assert response.status_code == 200

    async def test_user_cannot_update_others(
        self,
        authenticated_client: AsyncClient,
        superuser: User,
    ):
        response = await authenticated_client.patch(
            f"/api/v1/users/{superuser.id}",
            json={"full_name": "Sneaky Update"},
        )
        assert response.status_code == 403


class TestDeleteUser:
    async def test_superuser_can_delete_user(
        self,
        superuser_client: AsyncClient,
        db_session: AsyncSession,
    ):
        from app.core.security import get_password_hash
        from app.models.user import User

        user_to_delete = User(
            email="todelete@example.com",
            username="deleteuser",
            hashed_password=get_password_hash("Password123!"),
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user_to_delete)
        await db_session.commit()
        await db_session.refresh(user_to_delete)

        response = await superuser_client.delete(f"/api/v1/users/{user_to_delete.id}")
        assert response.status_code == 204

    async def test_regular_user_cannot_delete(
        self,
        authenticated_client: AsyncClient,
        superuser: User,
    ):
        response = await authenticated_client.delete(f"/api/v1/users/{superuser.id}")
        assert response.status_code == 403
