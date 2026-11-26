from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate

# Compared against when the email is unknown, so a failed login takes the same
# time whether or not the account exists.
_DUMMY_HASH = get_password_hash("timing-equaliser-not-a-real-password", rounds=12)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

    async def register(self, user_create: UserCreate) -> User:
        if await self.user_repo.get_by_email(user_create.email):
            raise ConflictError("Email already registered")
        if await self.user_repo.get_by_username(user_create.username):
            raise ConflictError("Username already taken")

        return await self.user_repo.create(
            email=user_create.email,
            username=user_create.username,
            hashed_password=get_password_hash(user_create.password),
            full_name=user_create.full_name,
        )

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(login_data.email)
        if user is None:
            verify_password(login_data.password, _DUMMY_HASH)
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        return self._issue_tokens(user)

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        payload = verify_token(refresh_token_str)
        if payload.token_type != "refresh":
            raise UnauthorizedError("Invalid token type")

        user = await self.user_repo.get_by_id(payload.sub)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return self._issue_tokens(user)

    @staticmethod
    def _issue_tokens(user: User) -> TokenResponse:
        claims = {"sub": user.id}
        return TokenResponse(
            access_token=create_access_token(claims),
            refresh_token=create_refresh_token(claims),
            token_type="bearer",
        )
