from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.core.clock import frozen_clock, utc_now


def test_utc_now_is_aware_utc() -> None:
    now = utc_now()
    assert now.tzinfo is UTC


def test_frozen_clock_pins_and_restores() -> None:
    at = datetime(2030, 1, 2, 3, 4, 5, tzinfo=UTC)
    with frozen_clock(at):
        assert utc_now() == at
    assert utc_now() != at


def test_frozen_clock_converts_to_utc() -> None:
    jakarta = timezone(timedelta(hours=7))
    with frozen_clock(datetime(2030, 1, 1, 7, 0, tzinfo=jakarta)) as frozen:
        assert frozen == datetime(2030, 1, 1, 0, 0, tzinfo=UTC)
        assert utc_now().tzinfo is UTC


def test_frozen_clock_rejects_naive() -> None:
    with pytest.raises(ValueError), frozen_clock(datetime(2030, 1, 1)):
        pass
