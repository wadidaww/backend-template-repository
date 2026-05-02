from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user."""
    service = AuthService(db)
    return await service.register(user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return JWT tokens."""
    service = AuthService(db)
    return await service.login(login_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a new access token using a valid refresh token."""
    service = AuthService(db)
    return await service.refresh_token(refresh_data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the currently authenticated user."""
    return current_user
