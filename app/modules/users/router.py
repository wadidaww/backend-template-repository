from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.common.exceptions import ForbiddenError
from app.common.schemas import PagedResponse, PaginationParams
from app.modules.auth.dependencies import CurrentUser, DbSession, Superuser
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=PagedResponse[UserResponse])
async def list_users(
    pagination: Annotated[PaginationParams, Depends()],
    db: DbSession,
    _: Superuser,
) -> PagedResponse[UserResponse]:
    """List all users (superuser only)."""
    users, total = await UserService(db).get_users(
        skip=pagination.skip, limit=pagination.limit
    )
    return PagedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        size=pagination.limit,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser) -> User:
    """Get the current user's profile."""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: DbSession, _: Superuser) -> User:
    """Get a user by ID (superuser only)."""
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str, user_data: UserUpdate, db: DbSession, current_user: CurrentUser
) -> User:
    """Update a user. Users can update themselves; superusers can update anyone."""
    if user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenError("Cannot update other users")
    if user_data.is_active is not None and not current_user.is_superuser:
        raise ForbiddenError("Only superusers can change account status")
    return await UserService(db).update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=204, response_class=Response)
async def delete_user(user_id: str, db: DbSession, _: Superuser) -> Response:
    """Delete a user (superuser only)."""
    await UserService(db).delete_user(user_id)
    return Response(status_code=204)
