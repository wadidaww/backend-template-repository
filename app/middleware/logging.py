from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        logger.info(
            "request_processed",
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response
