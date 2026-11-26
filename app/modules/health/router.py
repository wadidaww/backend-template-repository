"""Liveness and readiness probes.

- ``/health/live``: the process is up. Never touches dependencies.
- ``/health/ready``: the database and Redis answer. Returns 503 otherwise,
  so a load balancer stops sending traffic until they recover.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.core import rate_limit
from app.core.config import get_settings
from app.core.redis import ping_redis
from app.db.session import ping_db

router = APIRouter(prefix="/health", tags=["health"])

CHECK_TIMEOUT_SECONDS = 2.0

Status = Literal["ok", "error"]


class LiveResponse(BaseModel):
    status: Status = "ok"
    version: str
    env: str


class ReadyResponse(BaseModel):
    status: Status
    checks: dict[str, Status]


async def _check(probe: Callable[[], Awaitable[None]]) -> Status:
    try:
        await asyncio.wait_for(probe(), timeout=CHECK_TIMEOUT_SECONDS)
    except Exception:
        return "error"
    return "ok"


# Readiness probes are exempt so a busy limiter never marks the app unhealthy.
CHECKS: dict[str, Callable[[], Awaitable[None]]] = {
    "database": ping_db,
    "redis": ping_redis,
}


@router.get("/live", response_model=LiveResponse)
@rate_limit.exempt
async def live() -> LiveResponse:
    settings = get_settings()
    return LiveResponse(version=settings.APP_VERSION, env=settings.APP_ENV)


@router.get("/ready", response_model=ReadyResponse)
@rate_limit.exempt
async def ready(response: Response) -> ReadyResponse:
    names = list(CHECKS)
    results = await asyncio.gather(*(_check(CHECKS[n]) for n in names))
    checks: dict[str, Status] = dict(zip(names, results, strict=True))
    overall: Status = "ok" if all(r == "ok" for r in results) else "error"
    if overall == "error":
        response.status_code = 503
    return ReadyResponse(status=overall, checks=checks)
