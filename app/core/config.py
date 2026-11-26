from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "testing", "staging", "production"]

# Default used only for local development; production refuses to start with it.
INSECURE_DEFAULT_SECRET = "change-this-secret-key-in-production-use-32-chars"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Backend Template API"
    APP_VERSION: str = "0.2.0"
    APP_ENV: AppEnv = "development"
    SECRET_KEY: str = Field(default=INSECURE_DEFAULT_SECRET, min_length=32)
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/backend_db"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, gt=0)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Rate limiting (applied to every route by default)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_TIMES: int = Field(default=100, gt=0)
    RATE_LIMIT_SECONDS: int = Field(default=60, gt=0)
    # "memory://" for a single process; use the Redis URL when running several
    # workers so limits are shared. Empty means "use REDIS_URL".
    RATE_LIMIT_STORAGE_URL: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def rate_limit(self) -> str:
        return f"{self.RATE_LIMIT_TIMES}/{self.RATE_LIMIT_SECONDS} seconds"

    @property
    def rate_limit_storage(self) -> str:
        if self.RATE_LIMIT_STORAGE_URL:
            return self.RATE_LIMIT_STORAGE_URL
        if self.is_testing:
            return "memory://"
        return self.REDIS_URL

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @model_validator(mode="after")
    def _check_production_safety(self) -> Self:
        if self.APP_ENV in ("staging", "production"):
            problems: list[str] = []
            if self.SECRET_KEY == INSECURE_DEFAULT_SECRET:
                problems.append("SECRET_KEY must be changed from the default")
            if "*" in self.allowed_origins_list:
                problems.append("ALLOWED_ORIGINS must not contain '*'")
            if self.DATABASE_URL.startswith("sqlite"):
                problems.append("DATABASE_URL must not use SQLite")
            if problems:
                raise ValueError(
                    f"Unsafe settings for APP_ENV={self.APP_ENV}: "
                    + "; ".join(problems)
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
