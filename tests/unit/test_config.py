from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import INSECURE_DEFAULT_SECRET, Settings

STRONG_SECRET = "x" * 48
PG_URL = "postgresql+asyncpg://u:p@db:5432/app"


def make(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "APP_ENV": "production",
        "SECRET_KEY": STRONG_SECRET,
        "DATABASE_URL": PG_URL,
        "ALLOWED_ORIGINS": "https://app.example.com",
        "RATE_LIMIT_STORAGE_URL": "",
    }
    values.update(overrides)
    # model_validate skips env vars and .env, so only these values apply.
    return Settings.model_validate(values)


class TestProductionSafety:
    def test_valid_production_settings(self) -> None:
        settings = make()
        assert settings.is_production

    def test_default_secret_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            make(SECRET_KEY=INSECURE_DEFAULT_SECRET)

    def test_wildcard_cors_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="ALLOWED_ORIGINS"):
            make(ALLOWED_ORIGINS="*")

    def test_sqlite_rejected_in_staging(self) -> None:
        with pytest.raises(ValidationError, match="SQLite"):
            make(APP_ENV="staging", DATABASE_URL="sqlite+aiosqlite:///x.db")

    def test_default_secret_allowed_in_development(self) -> None:
        assert make(APP_ENV="development", SECRET_KEY=INSECURE_DEFAULT_SECRET)

    def test_short_secret_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make(SECRET_KEY="too-short")

    def test_unknown_env_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make(APP_ENV="prod")


class TestDerivedValues:
    def test_rate_limit_string(self) -> None:
        settings = make(RATE_LIMIT_TIMES=5, RATE_LIMIT_SECONDS=30)
        assert settings.rate_limit == "5/30 seconds"

    def test_rate_limit_storage_defaults_to_redis(self) -> None:
        settings = make(REDIS_URL="redis://cache:6379/0")
        assert settings.rate_limit_storage == "redis://cache:6379/0"

    def test_rate_limit_storage_memory_in_tests(self) -> None:
        assert make(APP_ENV="testing").rate_limit_storage == "memory://"
