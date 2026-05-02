"""Calendar / date-time utility helpers.

All helpers are pure functions with no side-effects so they are trivially
testable without a running database or HTTP server.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Days that are considered part of the working week (Mon=0 … Fri=4).
_WORKING_WEEKDAYS: frozenset[int] = frozenset(range(5))


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """Return *d* formatted as a string.

    Args:
        d: The date to format.
        fmt: ``strftime``-compatible format string.  Defaults to ISO 8601.

    Returns:
        Formatted date string.

    Example::

        >>> format_date(date(2024, 1, 5))
        '2024-01-05'
        >>> format_date(date(2024, 1, 5), "%d/%m/%Y")
        '05/01/2024'
    """
    return d.strftime(fmt)


def format_datetime(
    dt: datetime,
    fmt: str = "%Y-%m-%dT%H:%M:%S",
    *,
    to_utc: bool = False,
) -> str:
    """Return *dt* formatted as a string, optionally converting to UTC first.

    Args:
        dt: The datetime to format.
        fmt: ``strftime``-compatible format string.
        to_utc: When ``True`` and *dt* is timezone-aware, convert to UTC
            before formatting.

    Returns:
        Formatted datetime string.
    """
    if to_utc and dt.tzinfo is not None:
        dt = dt.astimezone(UTC)
    return dt.strftime(fmt)


# ---------------------------------------------------------------------------
# Range helpers
# ---------------------------------------------------------------------------


def date_range(start: date, end: date, *, step_days: int = 1) -> Iterator[date]:
    """Yield every date from *start* up to (but **not** including) *end*.

    Args:
        start: First date to yield.
        end: Upper bound (exclusive).
        step_days: Number of days between successive yields.  Must be ≥ 1.

    Yields:
        ``date`` objects.

    Raises:
        ValueError: If *step_days* is less than 1.

    Example::

        >>> list(date_range(date(2024, 1, 1), date(2024, 1, 4)))
        [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2), datetime.date(2024, 1, 3)]
    """
    if step_days < 1:
        raise ValueError(f"step_days must be >= 1, got {step_days}")
    step = timedelta(days=step_days)
    current = start
    while current < end:
        yield current
        current += step


# ---------------------------------------------------------------------------
# Working-day helpers
# ---------------------------------------------------------------------------


def is_working_day(d: date, *, holidays: set[date] | None = None) -> bool:
    """Return ``True`` if *d* is a Monday-to-Friday non-holiday.

    Args:
        d: The date to check.
        holidays: An optional set of dates to treat as non-working.

    Returns:
        ``True`` when *d* is a weekday that is not in *holidays*.
    """
    if d.weekday() not in _WORKING_WEEKDAYS:
        return False
    if holidays and d in holidays:
        return False
    return True


def working_days_between(
    start: date,
    end: date,
    *,
    holidays: set[date] | None = None,
) -> int:
    """Count the working days in the half-open interval ``[start, end)``.

    Args:
        start: Start of the interval (inclusive).
        end: End of the interval (exclusive).
        holidays: Optional set of holiday dates to exclude.

    Returns:
        Number of working days.
    """
    return sum(
        1 for d in date_range(start, end) if is_working_day(d, holidays=holidays)
    )


def next_working_day(
    d: date,
    *,
    holidays: set[date] | None = None,
) -> date:
    """Return the first working day strictly after *d*.

    Args:
        d: Reference date.
        holidays: Optional set of holiday dates to skip.

    Returns:
        The next working day.
    """
    candidate = d + timedelta(days=1)
    while not is_working_day(candidate, holidays=holidays):
        candidate += timedelta(days=1)
    return candidate


# ---------------------------------------------------------------------------
# Human-readable duration
# ---------------------------------------------------------------------------


def humanize_timedelta(delta: timedelta) -> str:
    """Return a short human-readable description of *delta*.

    The description uses the largest applicable unit (days, hours, minutes,
    or seconds).  For durations less than a second "just now" is returned.

    Args:
        delta: A ``timedelta`` object.  Negative deltas are treated as their
            absolute value.

    Returns:
        A human-readable string such as ``"3 days"``, ``"2 hours"``,
        ``"5 minutes"``, ``"30 seconds"``, or ``"just now"``.

    Example::

        >>> humanize_timedelta(timedelta(seconds=90))
        '1 minute'
        >>> humanize_timedelta(timedelta(days=2))
        '2 days'
    """
    total_seconds = int(abs(delta.total_seconds()))

    if total_seconds < 1:
        return "just now"

    units: list[tuple[int, str]] = [
        (86400, "day"),
        (3600, "hour"),
        (60, "minute"),
        (1, "second"),
    ]
    for seconds_per_unit, name in units:
        value = total_seconds // seconds_per_unit
        if value >= 1:
            return f"{value} {name}{'s' if value != 1 else ''}"

    return "just now"  # pragma: no cover


# ---------------------------------------------------------------------------
# Timezone conversion
# ---------------------------------------------------------------------------


def to_timezone(dt: datetime, tz: timezone | str) -> datetime:
    """Convert an aware *dt* to *tz*.

    Args:
        dt: A timezone-aware ``datetime``.
        tz: Target timezone as a ``datetime.timezone`` instance or an IANA
            string such as ``"UTC"`` (only ``"UTC"`` is supported without
            third-party libraries).

    Returns:
        The converted ``datetime``.

    Raises:
        ValueError: If *dt* is naïve (has no timezone info), or if an
            unrecognised string is passed for *tz*.
    """
    if dt.tzinfo is None:
        raise ValueError(
            "dt must be timezone-aware; use utcnow() or attach tzinfo first."
        )
    if isinstance(tz, str):
        if tz.upper() == "UTC":
            tz = UTC
        else:
            raise ValueError(
                f"String timezone '{tz}' is not supported without a third-party library "
                "(e.g. zoneinfo or pytz).  Pass a datetime.timezone object instead."
            )
    return dt.astimezone(tz)
