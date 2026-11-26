from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import get_settings

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Return the shared client (connections are opened lazily)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            get_settings().REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def ping_redis() -> None:
    """Raise if Redis is unreachable."""
    await get_redis_client().ping()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    yield get_redis_client()


class RedisClient:
    """Thin typed wrapper for string values."""

    def __init__(self, client: aioredis.Redis) -> None:
        self.client = client

    async def get(self, key: str) -> str | None:
        value = await self.client.get(key)
        return None if value is None else str(value)

    async def set(self, key: str, value: str, expire: int | None = None) -> None:
        await self.client.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))
