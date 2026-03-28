from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.base import ConflictError, UnauthorizedError
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate
from app.services.auth import AuthService


def make_mock_user(
    user_id: str = "user-id-1",
    email: str = "test@example.com",
    password: str = "hashed_password",
    is_active: bool = True,
):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.hashed_password = password
    user.is_active = is_active
    return user


class TestAuthService:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AuthService(session=mock_session)

    async def test_register_creates_user(self, service):
        mock_user = make_mock_user()
        with (
            patch.object(service.user_repo, "get_by_email", return_value=None),
            patch.object(service.user_repo, "get_by_username", return_value=None),
            patch.object(service.user_repo, "create", return_value=mock_user),
        ):
            result = await service.register(
                UserCreate(
                    email="new@example.com",
                    username="newuser",
                    password="Password123!",
                )
            )
            assert result == mock_user

    async def test_register_duplicate_email_raises(self, service):
        existing = make_mock_user()
        with patch.object(service.user_repo, "get_by_email", return_value=existing):
            with pytest.raises(ConflictError, match="Email already registered"):
                await service.register(
                    UserCreate(
                        email="existing@example.com",
                        username="newuser",
                        password="Password123!",
                    )
                )

    async def test_register_duplicate_username_raises(self, service):
        existing = make_mock_user()
        with (
            patch.object(service.user_repo, "get_by_email", return_value=None),
            patch.object(service.user_repo, "get_by_username", return_value=existing),
        ):
            with pytest.raises(ConflictError, match="Username already taken"):
                await service.register(
                    UserCreate(
                        email="new@example.com",
                        username="takenuser",
                        password="Password123!",
                    )
                )

    async def test_login_with_valid_credentials(self, service):
        from app.core.security import get_password_hash

        hashed = get_password_hash("Password123!")
        mock_user = make_mock_user(password=hashed)

        with patch.object(service.user_repo, "get_by_email", return_value=mock_user):
            result = await service.login(
                LoginRequest(email="test@example.com", password="Password123!")
            )
            assert result.access_token
            assert result.refresh_token
            assert result.token_type == "bearer"

    async def test_login_wrong_password_raises(self, service):
        from app.core.security import get_password_hash

        hashed = get_password_hash("CorrectPassword!")
        mock_user = make_mock_user(password=hashed)

        with patch.object(service.user_repo, "get_by_email", return_value=mock_user):
            with pytest.raises(UnauthorizedError):
                await service.login(
                    LoginRequest(email="test@example.com", password="WrongPassword!")
                )

    async def test_login_nonexistent_user_raises(self, service):
        with patch.object(service.user_repo, "get_by_email", return_value=None):
            with pytest.raises(UnauthorizedError):
                await service.login(
                    LoginRequest(email="nobody@example.com", password="Password123!")
                )

    async def test_login_inactive_user_raises(self, service):
        from app.core.security import get_password_hash

        hashed = get_password_hash("Password123!")
        mock_user = make_mock_user(password=hashed, is_active=False)

        with patch.object(service.user_repo, "get_by_email", return_value=mock_user):
            with pytest.raises(UnauthorizedError, match="inactive"):
                await service.login(
                    LoginRequest(email="test@example.com", password="Password123!")
                )
