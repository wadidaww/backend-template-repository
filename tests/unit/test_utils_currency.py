"""Unit tests for app.utils.currency."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.utils.currency import (
    cents_to_decimal,
    convert_currency,
    decimal_to_cents,
    format_currency,
    parse_currency,
    round_currency,
)

# ---------------------------------------------------------------------------
# round_currency
# ---------------------------------------------------------------------------


class TestRoundCurrency:
    def test_rounds_half_up(self):
        assert round_currency(Decimal("1.235")) == Decimal("1.24")

    def test_rounds_down(self):
        assert round_currency(Decimal("1.234")) == Decimal("1.23")

    def test_zero_decimal_places(self):
        assert round_currency(Decimal("1.6"), 0) == Decimal("2")

    def test_three_decimal_places(self):
        assert round_currency(Decimal("1.2345"), 3) == Decimal("1.235")

    def test_exact_value_unchanged(self):
        assert round_currency(Decimal("1.50")) == Decimal("1.50")

    def test_negative_decimal_places_raises(self):
        with pytest.raises(ValueError, match="decimal_places"):
            round_currency(Decimal("1.0"), -1)

    def test_negative_amount(self):
        assert round_currency(Decimal("-1.235")) == Decimal("-1.24")


# ---------------------------------------------------------------------------
# decimal_to_cents / cents_to_decimal
# ---------------------------------------------------------------------------


class TestMinorUnits:
    def test_decimal_to_cents(self):
        assert decimal_to_cents(Decimal("12.34")) == 1234

    def test_decimal_to_cents_rounds(self):
        assert decimal_to_cents(Decimal("12.345")) == 1235

    def test_decimal_to_cents_zero(self):
        assert decimal_to_cents(Decimal("0.00")) == 0

    def test_decimal_to_cents_three_places(self):
        assert decimal_to_cents(Decimal("12.345"), decimal_places=3) == 12345

    def test_cents_to_decimal(self):
        assert cents_to_decimal(1234) == Decimal("12.34")

    def test_cents_to_decimal_zero(self):
        assert cents_to_decimal(0) == Decimal("0")

    def test_cents_to_decimal_large(self):
        assert cents_to_decimal(100000) == Decimal("1000.00")

    def test_roundtrip(self):
        original = Decimal("99.99")
        assert cents_to_decimal(decimal_to_cents(original)) == original


# ---------------------------------------------------------------------------
# format_currency
# ---------------------------------------------------------------------------


class TestFormatCurrency:
    def test_usd_default(self):
        assert format_currency(Decimal("1234.50")) == "$1,234.50"

    def test_eur_after(self):
        result = format_currency(Decimal("1234.50"), "EUR", symbol_position="after")
        assert result == "1,234.50 €"

    def test_gbp(self):
        assert format_currency(Decimal("99.99"), "GBP") == "£99.99"

    def test_negative_amount(self):
        assert format_currency(Decimal("-50.00")) == "$-50.00"

    def test_custom_symbol(self):
        result = format_currency(Decimal("10.00"), symbol="€€")
        assert result == "€€10.00"

    def test_zero_decimal_places(self):
        result = format_currency(Decimal("1234"), "JPY", decimal_places=0)
        assert result == "¥1,234"

    def test_custom_separators(self):
        result = format_currency(
            Decimal("1234.56"),
            thousands_sep=".",
            decimal_sep=",",
        )
        assert result == "$1.234,56"

    def test_int_input(self):
        assert format_currency(100) == "$100.00"

    def test_float_input(self):
        assert format_currency(9.99) == "$9.99"

    def test_unknown_currency_code_uses_code_as_symbol(self):
        result = format_currency(Decimal("1.00"), "XYZ")
        assert result.startswith("XYZ")

    def test_invalid_symbol_position_raises(self):
        with pytest.raises(ValueError, match="symbol_position"):
            format_currency(Decimal("1.00"), symbol_position="middle")

    def test_thousands_grouping(self):
        result = format_currency(Decimal("1234567.89"))
        assert result == "$1,234,567.89"


# ---------------------------------------------------------------------------
# parse_currency
# ---------------------------------------------------------------------------


class TestParseCurrency:
    def test_plain_number(self):
        assert parse_currency("42.5") == Decimal("42.5")

    def test_usd_with_comma(self):
        assert parse_currency("$1,234.56") == Decimal("1234.56")

    def test_eur_symbol(self):
        assert parse_currency("€9.99") == Decimal("9.99")

    def test_negative_gbp(self):
        assert parse_currency("-£99.99") == Decimal("-99.99")

    def test_whitespace_stripped(self):
        assert parse_currency("  10.00  ") == Decimal("10.00")

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_currency("not-a-number")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_currency("$")


# ---------------------------------------------------------------------------
# convert_currency
# ---------------------------------------------------------------------------


class TestConvertCurrency:
    def test_basic_conversion(self):
        result = convert_currency(Decimal("100"), Decimal("1.08"))
        assert result == Decimal("108.00")

    def test_rounds_result(self):
        result = convert_currency(Decimal("1"), Decimal("3"))
        assert result == Decimal("3.00")

    def test_non_default_decimal_places(self):
        result = convert_currency(Decimal("100"), Decimal("1.234"), decimal_places=3)
        assert result == Decimal("123.400")

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError, match="positive"):
            convert_currency(Decimal("100"), Decimal("0"))

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="positive"):
            convert_currency(Decimal("100"), Decimal("-1.5"))
