"""Migrations apply cleanly and match the SQLAlchemy models."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import get_settings

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def alembic_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Config]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'mig.db'}")
    get_settings.cache_clear()
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "app/db/migrations"))
    yield cfg
    get_settings.cache_clear()


def test_upgrade_downgrade_and_no_model_drift(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    # Fails if the models have changes that no migration covers.
    command.check(alembic_config)
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
