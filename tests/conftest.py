"""
Pytest configuration and shared fixtures.

Environment variables are set at the very top so they are in place before any
app module is imported (app modules read settings at import time via lru_cache).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Set test env-vars BEFORE importing any app module
# ---------------------------------------------------------------------------
os.environ.update(
    {
        "APP_ENV": "testing",
        "DATABASE_URL": "sqlite+aiosqlite:///./test_app.db",
        "TEST_DATABASE_URL": "sqlite+aiosqlite:///./test_app.db",
        "SECRET_KEY": "test-secret-key-for-testing-only-not-for-production",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "RATE_LIMIT_TIMES": "1000",
        "RATE_LIMIT_SECONDS": "60",
    }
)

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Clear the settings cache so test env-vars are picked up
from app.core.config import get_settings

get_settings.cache_clear()

from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

# ---------------------------------------------------------------------------
# Test database engine (SQLite, isolated per test run)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///./test_app.db"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database for every test by creating/dropping all tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with the database dependency overridden."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create and persist a standard (non-superuser) test user."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("Test1234!"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def superuser(db_session: AsyncSession) -> User:
    """Create and persist a superuser test user."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("Admin1234!"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
    client: AsyncClient,
    test_user: User,
) -> AsyncClient:
    """HTTP client pre-authenticated as the standard test user."""
    token = create_access_token({"sub": test_user.id})
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def superuser_client(
    client: AsyncClient,
    superuser: User,
) -> AsyncClient:
    """HTTP client pre-authenticated as a superuser."""
    token = create_access_token({"sub": superuser.id})
    client.headers["Authorization"] = f"Bearer {token}"
    return client
