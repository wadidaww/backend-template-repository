"""A single source of "now" so code is UTC-aware and tests can freeze time.

Use ``utc_now()`` instead of ``datetime.now()`` / ``datetime.utcnow()``.
In tests, ``with frozen_clock(datetime(...)):`` pins the value.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

_now_factory: Callable[[], datetime] = lambda: datetime.now(UTC)  # noqa: E731


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return _now_factory()


def set_clock(factory: Callable[[], datetime]) -> None:
    global _now_factory
    _now_factory = factory


def reset_clock() -> None:
    set_clock(lambda: datetime.now(UTC))


@contextmanager
def frozen_clock(at: datetime) -> Iterator[datetime]:
    """Pin ``utc_now()`` to ``at`` (must be timezone-aware) inside the block."""
    if at.tzinfo is None:
        raise ValueError("frozen_clock requires a timezone-aware datetime")
    previous = _now_factory
    frozen = at.astimezone(UTC)
    set_clock(lambda: frozen)
    try:
        yield frozen
    finally:
        set_clock(previous)
