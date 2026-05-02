from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-secret-key-in-production-use-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/backend_db"
    )
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test_app.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Rate Limiting
    RATE_LIMIT_TIMES: int = 100
    RATE_LIMIT_SECONDS: int = 60

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
