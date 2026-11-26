from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.common.exceptions import AppException

logger = structlog.get_logger(__name__)

_JSON_SAFE = (str, int, float, bool, type(None))


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppException)
    logger.warning(
        "app_exception",
        status_code=exc.status_code,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Pydantic error "ctx" may hold non-JSON objects (e.g. exceptions).
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        err = {k: v for k, v in error.items() if k != "ctx"}
        if "ctx" in error:
            err["ctx"] = {
                k: v if isinstance(v, _JSON_SAFE) else str(v)
                for k, v in error["ctx"].items()
            }
        errors.append(err)
    return JSONResponse(status_code=422, content={"detail": errors})


async def rate_limit_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RateLimitExceeded)
    response = JSONResponse(
        status_code=429, content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )
    limiter = getattr(request.app.state, "limiter", None)
    view_limit = getattr(request.state, "view_rate_limit", None)
    if limiter is not None and view_limit is not None:
        response = limiter._inject_headers(response, view_limit)
    return response


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
