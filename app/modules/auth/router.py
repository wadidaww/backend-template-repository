from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.core import rate_limit
from app.modules.auth.dependencies import CurrentUser, DbSession
from app.modules.auth.schemas import LoginRequest, RefreshTokenRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Routes with a custom limit must accept ``request`` and ``response``.
# Stricter limits on credential endpoints to slow down brute force attempts.
AUTH_LIMIT = "10/minute"


@router.post("/register", response_model=UserResponse, status_code=201)
@rate_limit.limit(AUTH_LIMIT)
async def register(
    request: Request, response: Response, user_data: UserCreate, db: DbSession
) -> User:
    """Register a new user."""
    return await AuthService(db).register(user_data)


@router.post("/login", response_model=TokenResponse)
@rate_limit.limit(AUTH_LIMIT)
async def login(
    request: Request, response: Response, login_data: LoginRequest, db: DbSession
) -> TokenResponse:
    """Authenticate and return JWT tokens."""
    return await AuthService(db).login(login_data)


@router.post("/refresh", response_model=TokenResponse)
@rate_limit.limit(AUTH_LIMIT)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_data: RefreshTokenRequest,
    db: DbSession,
) -> TokenResponse:
    """Issue a new token pair using a valid refresh token."""
    return await AuthService(db).refresh_token(refresh_data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    """Return the currently authenticated user."""
    return current_user
