from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user, require_superuser
from app.dependencies.db import get_db
from app.exceptions.base import ForbiddenError
from app.models.user import User
from app.schemas.common import PagedResponse, PaginationParams
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=PagedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superuser),
) -> PagedResponse[UserResponse]:
    """List all users (superuser only)."""
    service = UserService(db)
    users, total = await service.get_users(skip=pagination.skip, limit=pagination.limit)
    return PagedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        size=pagination.limit,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current user's profile."""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superuser),
) -> User:
    """Get a user by ID (superuser only)."""
    service = UserService(db)
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Update a user. Users can update themselves; superusers can update anyone."""
    if user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenError("Cannot update other users")
    service = UserService(db)
    return await service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=204, response_class=Response)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superuser),
) -> Response:
    """Delete a user (superuser only)."""
    service = UserService(db)
    await service.delete_user(user_id)
    return Response(status_code=204)
