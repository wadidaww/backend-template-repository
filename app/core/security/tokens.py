"""Locally issued JWTs (HS256/384/512) for email/password login."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any, Literal

import jwt

from app.common.exceptions import UnauthorizedError
from app.core.clock import utc_now
from app.core.config import get_settings
from app.modules.auth.schemas import TokenPayload

TokenType = Literal["access", "refresh"]


def _create_token(
    data: dict[str, Any], token_type: TokenType, expires_delta: timedelta
) -> str:
    settings = get_settings()
    now = utc_now()
    to_encode = {
        **data,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid.uuid4().hex,
        "token_type": token_type,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    settings = get_settings()
    return _create_token(
        data,
        "access",
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    settings = get_settings()
    return _create_token(
        data,
        "refresh",
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def verify_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token") from exc

    return TokenPayload(
        sub=str(payload["sub"]),
        exp=payload.get("exp"),
        token_type=payload.get("token_type", "access"),
    )
