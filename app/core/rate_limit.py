"""Global rate limiting (slowapi).

Every route gets the default limit from settings. Override per route with
``@limiter.limit("5/minute")`` or opt out with ``@limiter.exempt``.
Requests are keyed by the bearer token when present, otherwise by client IP.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any, cast

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import get_settings


def rate_limit_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        digest = hashlib.sha256(auth[7:].encode()).hexdigest()[:32]
        return f"token:{digest}"
    return f"ip:{get_remote_address(request)}"


def create_limiter() -> Limiter:
    settings = get_settings()
    return Limiter(
        key_func=rate_limit_key,
        default_limits=[settings.rate_limit],
        storage_uri=settings.rate_limit_storage,
        enabled=settings.RATE_LIMIT_ENABLED,
        headers_enabled=True,
    )


limiter = create_limiter()


def limit[F: Callable[..., Any]](limit_value: str) -> Callable[[F], F]:
    """Typed wrapper for ``limiter.limit`` (the route must take ``request``)."""
    return cast(Callable[[F], F], limiter.limit(limit_value))


def exempt[F: Callable[..., Any]](func: F) -> F:
    """Typed wrapper for ``limiter.exempt``."""
    return cast(F, limiter.exempt(func))  # type: ignore[no-untyped-call]
