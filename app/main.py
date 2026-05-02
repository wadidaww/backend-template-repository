from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import close_db, init_db
from app.exceptions.handlers import add_exception_handlers
from app.middleware.logging import LoggingMiddleware

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.APP_ENV)

    init_db(
        settings.DATABASE_URL,
        echo=settings.is_development,
    )
    logger.info("application_startup", env=settings.APP_ENV)

    yield

    await close_db()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Backend Template API",
        description="Production-ready FastAPI backend template",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Rate limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request / response logging
    app.add_middleware(LoggingMiddleware)

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next) -> JSONResponse:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # Custom exception handlers
    add_exception_handlers(app)

    # Versioned API routes
    app.include_router(api_router, prefix="/api/v1")

    # Root health check
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        return {"status": "ok", "env": settings.APP_ENV}

    return app


app = create_app()
