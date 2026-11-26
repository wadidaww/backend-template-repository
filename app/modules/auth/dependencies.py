from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import verify_token
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = verify_token(token)
    if payload.token_type != "access":
        raise UnauthorizedError("Invalid token type")
    user = await UserRepository(db).get_by_id(payload.sub)
    if user is None:
        raise UnauthorizedError("User not found")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise UnauthorizedError("Inactive user")
    return current_user


async def require_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not current_user.is_superuser:
        raise ForbiddenError("Superuser access required")
    return current_user


CurrentUser = Annotated[User, Depends(get_current_active_user)]
Superuser = Annotated[User, Depends(require_superuser)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
