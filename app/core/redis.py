from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis

_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    from app.core.config import get_settings

    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = await get_redis_client()
    yield client


class RedisClient:
    def __init__(self, client: aioredis.Redis) -> None:
        self.client = client

    async def get(self, key: str) -> Any | None:
        return await self.client.get(key)

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        await self.client.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))
