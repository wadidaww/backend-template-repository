from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.exceptions.base import ConflictError, UnauthorizedError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(User, session)

    async def register(self, user_create: UserCreate) -> User:
        if await self.user_repo.get_by_email(user_create.email):
            raise ConflictError("Email already registered")

        if await self.user_repo.get_by_username(user_create.username):
            raise ConflictError("Username already taken")

        hashed_password = get_password_hash(user_create.password)
        return await self.user_repo.create(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
        )

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        from app.core.config import get_settings

        settings = get_settings()
        user = await self.user_repo.get_by_email(login_data.email)

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is inactive")

        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        from app.core.config import get_settings

        settings = get_settings()
        payload = verify_token(refresh_token_str)

        if payload.token_type != "refresh":
            raise UnauthorizedError("Invalid token type")

        user = await self.user_repo.get_by_id(payload.sub)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.id},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
