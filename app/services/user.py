from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(User, session)

    async def get_user(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def get_users(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[User], int]:
        users = await self.user_repo.get_all(skip=skip, limit=limit)
        total = await self.user_repo.count()
        return users, total

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        update_data = user_data.model_dump(exclude_unset=True)
        return await self.user_repo.update(user, **update_data)

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user(user_id)
        await self.user_repo.delete(user)
