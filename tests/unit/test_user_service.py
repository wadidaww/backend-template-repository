from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.base import NotFoundError
from app.schemas.user import UserUpdate
from app.services.user import UserService


def make_mock_user(
    user_id: str = "test-user-id",
    email: str = "user@example.com",
    username: str = "testuser",
    is_active: bool = True,
):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.username = username
    user.is_active = is_active
    return user


class TestUserService:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return UserService(session=mock_session)

    async def test_get_user_returns_user(self, service, mock_session):
        mock_user = make_mock_user()
        with patch.object(
            service.user_repo, "get_by_id", return_value=mock_user
        ) as mock_get:
            result = await service.get_user("test-user-id")
            mock_get.assert_called_once_with("test-user-id")
            assert result == mock_user

    async def test_get_user_not_found_raises(self, service):
        with patch.object(service.user_repo, "get_by_id", return_value=None):
            with pytest.raises(NotFoundError):
                await service.get_user("nonexistent-id")

    async def test_get_users_returns_list_and_total(self, service):
        mock_users = [make_mock_user(user_id=str(i)) for i in range(3)]
        with (
            patch.object(service.user_repo, "get_all", return_value=mock_users),
            patch.object(service.user_repo, "count", return_value=3),
        ):
            users, total = await service.get_users(skip=0, limit=10)
            assert len(users) == 3
            assert total == 3

    async def test_update_user_calls_repository(self, service):
        mock_user = make_mock_user()
        updated_user = make_mock_user(email="new@example.com")
        with (
            patch.object(service.user_repo, "get_by_id", return_value=mock_user),
            patch.object(
                service.user_repo, "update", return_value=updated_user
            ) as mock_update,
        ):
            result = await service.update_user(
                "test-user-id", UserUpdate(email="new@example.com")
            )
            mock_update.assert_called_once()
            assert result == updated_user

    async def test_delete_user_calls_repository(self, service):
        mock_user = make_mock_user()
        with (
            patch.object(service.user_repo, "get_by_id", return_value=mock_user),
            patch.object(service.user_repo, "delete", return_value=None) as mock_del,
        ):
            await service.delete_user("test-user-id")
            mock_del.assert_called_once_with(mock_user)

    async def test_delete_nonexistent_user_raises(self, service):
        with patch.object(service.user_repo, "get_by_id", return_value=None):
            with pytest.raises(NotFoundError):
                await service.delete_user("nonexistent-id")
