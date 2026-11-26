from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictError, NotFoundError
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

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

        new_email = update_data.get("email")
        if new_email and new_email != user.email:
            if await self.user_repo.get_by_email(new_email):
                raise ConflictError("Email already registered")
        new_username = update_data.get("username")
        if new_username and new_username != user.username:
            if await self.user_repo.get_by_username(new_username):
                raise ConflictError("Username already taken")

        return await self.user_repo.update(user, **update_data)

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user(user_id)
        await self.user_repo.delete(user)
