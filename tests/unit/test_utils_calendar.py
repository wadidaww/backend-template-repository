"""Unit tests for app.utils.calendar."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from app.utils.calendar import (
    date_range,
    format_date,
    format_datetime,
    humanize_timedelta,
    is_working_day,
    next_working_day,
    to_timezone,
    working_days_between,
)

# ---------------------------------------------------------------------------
# format_date
# ---------------------------------------------------------------------------


class TestFormatDate:
    def test_iso_default(self):
        assert format_date(date(2024, 1, 5)) == "2024-01-05"

    def test_custom_format(self):
        assert format_date(date(2024, 1, 5), "%d/%m/%Y") == "05/01/2024"

    def test_single_digit_padding(self):
        assert format_date(date(2024, 3, 7), "%m-%d") == "03-07"

    def test_year_only(self):
        assert format_date(date(2024, 6, 15), "%Y") == "2024"


# ---------------------------------------------------------------------------
# format_datetime
# ---------------------------------------------------------------------------


class TestFormatDatetime:
    def test_default_format(self):
        dt = datetime(2024, 6, 15, 12, 30, 45)
        assert format_datetime(dt) == "2024-06-15T12:30:45"

    def test_custom_format(self):
        dt = datetime(2024, 6, 15, 9, 5, 3)
        assert format_datetime(dt, "%H:%M:%S") == "09:05:03"

    def test_to_utc_converts_aware(self):
        # Create a datetime 2 hours ahead of UTC
        tz_plus2 = timezone(timedelta(hours=2))
        dt = datetime(2024, 6, 15, 14, 0, 0, tzinfo=tz_plus2)
        result = format_datetime(dt, "%H:%M:%S", to_utc=True)
        assert result == "12:00:00"

    def test_to_utc_flag_ignored_for_naive(self):
        dt = datetime(2024, 6, 15, 12, 0, 0)
        # naive dt: to_utc has no effect (no conversion can happen)
        result = format_datetime(dt, to_utc=True)
        assert result == "2024-06-15T12:00:00"


# ---------------------------------------------------------------------------
# date_range
# ---------------------------------------------------------------------------


class TestDateRange:
    def test_single_day(self):
        r = list(date_range(date(2024, 1, 1), date(2024, 1, 2)))
        assert r == [date(2024, 1, 1)]

    def test_three_days(self):
        r = list(date_range(date(2024, 1, 1), date(2024, 1, 4)))
        assert r == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]

    def test_empty_when_start_equals_end(self):
        r = list(date_range(date(2024, 1, 1), date(2024, 1, 1)))
        assert r == []

    def test_empty_when_start_after_end(self):
        r = list(date_range(date(2024, 1, 5), date(2024, 1, 1)))
        assert r == []

    def test_step_two(self):
        r = list(date_range(date(2024, 1, 1), date(2024, 1, 7), step_days=2))
        assert r == [date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 5)]

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError, match="step_days"):
            list(date_range(date(2024, 1, 1), date(2024, 1, 5), step_days=0))


# ---------------------------------------------------------------------------
# is_working_day
# ---------------------------------------------------------------------------


class TestIsWorkingDay:
    def test_monday_is_working(self):
        assert is_working_day(date(2024, 1, 8)) is True  # Monday

    def test_friday_is_working(self):
        assert is_working_day(date(2024, 1, 12)) is True  # Friday

    def test_saturday_not_working(self):
        assert is_working_day(date(2024, 1, 13)) is False  # Saturday

    def test_sunday_not_working(self):
        assert is_working_day(date(2024, 1, 14)) is False  # Sunday

    def test_holiday_is_not_working(self):
        xmas = date(2024, 12, 25)  # Wednesday
        assert is_working_day(xmas, holidays={xmas}) is False

    def test_weekday_without_holiday_set(self):
        # No holidays kwarg supplied – normal weekday should be True
        assert is_working_day(date(2024, 1, 8)) is True


# ---------------------------------------------------------------------------
# working_days_between
# ---------------------------------------------------------------------------


class TestWorkingDaysBetween:
    def test_full_week(self):
        # Mon–Fri = 5 working days; end is exclusive
        start = date(2024, 1, 8)  # Monday
        end = date(2024, 1, 13)  # Saturday (exclusive)
        assert working_days_between(start, end) == 5

    def test_weekend_excluded(self):
        start = date(2024, 1, 8)  # Monday
        end = date(2024, 1, 15)  # Next Monday (exclusive)
        assert working_days_between(start, end) == 5

    def test_with_holiday(self):
        start = date(2024, 1, 8)  # Monday
        end = date(2024, 1, 13)  # Saturday (exclusive)
        holiday = date(2024, 1, 10)  # Wednesday
        assert working_days_between(start, end, holidays={holiday}) == 4

    def test_zero_for_same_dates(self):
        d = date(2024, 1, 8)
        assert working_days_between(d, d) == 0


# ---------------------------------------------------------------------------
# next_working_day
# ---------------------------------------------------------------------------


class TestNextWorkingDay:
    def test_from_friday_skips_weekend(self):
        friday = date(2024, 1, 12)
        assert next_working_day(friday) == date(2024, 1, 15)  # Monday

    def test_from_monday_is_tuesday(self):
        monday = date(2024, 1, 8)
        assert next_working_day(monday) == date(2024, 1, 9)

    def test_skips_holiday(self):
        friday = date(2024, 1, 12)
        # Suppose next Monday is also a holiday
        monday = date(2024, 1, 15)
        assert next_working_day(friday, holidays={monday}) == date(2024, 1, 16)

    def test_from_thursday_is_friday(self):
        thursday = date(2024, 1, 11)
        assert next_working_day(thursday) == date(2024, 1, 12)


# ---------------------------------------------------------------------------
# humanize_timedelta
# ---------------------------------------------------------------------------


class TestHumanizeTimedelta:
    def test_just_now(self):
        assert humanize_timedelta(timedelta(seconds=0)) == "just now"

    def test_one_second(self):
        assert humanize_timedelta(timedelta(seconds=1)) == "1 second"

    def test_plural_seconds(self):
        assert humanize_timedelta(timedelta(seconds=45)) == "45 seconds"

    def test_one_minute(self):
        assert humanize_timedelta(timedelta(seconds=90)) == "1 minute"

    def test_plural_minutes(self):
        assert humanize_timedelta(timedelta(minutes=5)) == "5 minutes"

    def test_one_hour(self):
        assert humanize_timedelta(timedelta(hours=1, minutes=30)) == "1 hour"

    def test_plural_hours(self):
        assert humanize_timedelta(timedelta(hours=3)) == "3 hours"

    def test_one_day(self):
        assert humanize_timedelta(timedelta(days=1)) == "1 day"

    def test_plural_days(self):
        assert humanize_timedelta(timedelta(days=10)) == "10 days"

    def test_negative_delta_treated_as_absolute(self):
        assert humanize_timedelta(timedelta(seconds=-90)) == "1 minute"


# ---------------------------------------------------------------------------
# to_timezone
# ---------------------------------------------------------------------------


class TestToTimezone:
    def test_convert_to_utc_string(self):
        tz_plus5 = timezone(timedelta(hours=5))
        dt = datetime(2024, 6, 15, 17, 0, 0, tzinfo=tz_plus5)
        result = to_timezone(dt, "UTC")
        assert result.hour == 12
        assert result.tzinfo == UTC

    def test_convert_to_timezone_object(self):
        tz_plus3 = timezone(timedelta(hours=3))
        tz_minus2 = timezone(timedelta(hours=-2))
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=tz_plus3)
        result = to_timezone(dt, tz_minus2)
        assert result.hour == 7

    def test_naive_datetime_raises(self):
        dt = datetime(2024, 6, 15, 12, 0, 0)  # no tzinfo
        with pytest.raises(ValueError, match="timezone-aware"):
            to_timezone(dt, "UTC")

    def test_unsupported_string_timezone_raises(self):
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="not supported"):
            to_timezone(dt, "America/New_York")
