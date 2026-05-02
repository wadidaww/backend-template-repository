"""Currency / money utility helpers.

All operations work with plain ``int`` (minor units / cents) or ``Decimal``
so there is no floating-point precision loss.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------


def round_currency(amount: Decimal, decimal_places: int = 2) -> Decimal:
    """Round *amount* to *decimal_places* using banker-friendly ROUND_HALF_UP.

    Args:
        amount: The monetary amount as a ``Decimal``.
        decimal_places: Number of decimal places to round to (default: 2).

    Returns:
        Rounded ``Decimal``.

    Raises:
        ValueError: If *decimal_places* is negative.

    Example::

        >>> round_currency(Decimal("1.235"))
        Decimal('1.24')
        >>> round_currency(Decimal("1.005"))
        Decimal('1.01')
    """
    if decimal_places < 0:
        raise ValueError(f"decimal_places must be >= 0, got {decimal_places}")
    quantize_str = Decimal(10) ** -decimal_places
    return amount.quantize(quantize_str, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Minor-unit encoding / decoding
# ---------------------------------------------------------------------------


def decimal_to_cents(amount: Decimal, decimal_places: int = 2) -> int:
    """Convert a decimal monetary amount to its integer minor-unit representation.

    For example ``Decimal("12.34")`` → ``1234`` for a 2-decimal-place currency.

    Args:
        amount: The decimal amount.
        decimal_places: Number of minor-unit decimal places (default: 2 for
            most currencies such as USD, EUR, GBP).

    Returns:
        Integer minor-unit value.

    Example::

        >>> decimal_to_cents(Decimal("12.34"))
        1234
        >>> decimal_to_cents(Decimal("12.345"), decimal_places=3)
        12345
    """
    rounded = round_currency(amount, decimal_places)
    return int(rounded * (Decimal(10) ** decimal_places))


def cents_to_decimal(cents: int, decimal_places: int = 2) -> Decimal:
    """Convert an integer minor-unit value back to a decimal amount.

    Args:
        cents: Integer minor-unit value.
        decimal_places: Number of minor-unit decimal places (default: 2).

    Returns:
        ``Decimal`` representation of the amount.

    Example::

        >>> cents_to_decimal(1234)
        Decimal('12.34')
    """
    return Decimal(cents) / (Decimal(10) ** decimal_places)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_currency(
    amount: Decimal | int | float,
    currency_code: str = "USD",
    *,
    symbol: str | None = None,
    decimal_places: int = 2,
    thousands_sep: str = ",",
    decimal_sep: str = ".",
    symbol_position: str = "before",
) -> str:
    """Format a monetary amount as a human-readable string.

    Args:
        amount: The amount to format.  ``int`` and ``float`` are converted to
            ``Decimal`` automatically (floats via their string representation
            to avoid floating-point surprises).
        currency_code: ISO 4217 currency code used when *symbol* is not
            provided.  A small built-in lookup table maps common codes to
            their symbols; unrecognised codes fall back to the code itself.
        symbol: Override the currency symbol.  When set, *currency_code* is
            not used for display purposes.
        decimal_places: Number of decimal places (default: 2).
        thousands_sep: Character used as the thousands separator.
        decimal_sep: Character used as the decimal separator.
        symbol_position: ``"before"`` (default) or ``"after"`` to control
            where the currency symbol is placed.

    Returns:
        Formatted string, e.g. ``"$1,234.56"`` or ``"1.234,56 €"``.

    Raises:
        ValueError: If *symbol_position* is not ``"before"`` or ``"after"``.

    Example::

        >>> format_currency(Decimal("1234.5"))
        '$1,234.50'
        >>> format_currency(Decimal("1234.5"), "EUR", symbol_position="after")
        '1,234.50 €'
    """
    if symbol_position not in ("before", "after"):
        raise ValueError(
            f"symbol_position must be 'before' or 'after', got {symbol_position!r}"
        )

    _SYMBOLS: dict[str, str] = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CNY": "¥",
        "KRW": "₩",
        "INR": "₹",
        "BTC": "₿",
    }

    if symbol is None:
        symbol = _SYMBOLS.get(currency_code.upper(), currency_code)

    if isinstance(amount, float):
        amount = Decimal(str(amount))
    else:
        amount = Decimal(amount)

    rounded = round_currency(amount, decimal_places)
    negative = rounded < 0
    abs_amount = abs(rounded)

    # Split into integer and fractional parts
    int_part, _, frac_part = f"{abs_amount:.{decimal_places}f}".partition(".")

    # Apply thousands separator
    groups: list[str] = []
    while len(int_part) > 3:
        groups.append(int_part[-3:])
        int_part = int_part[:-3]
    groups.append(int_part)
    formatted_int = thousands_sep.join(reversed(groups))

    # Reassemble
    number_str = (
        f"{formatted_int}{decimal_sep}{frac_part}"
        if decimal_places > 0
        else formatted_int
    )
    if negative:
        number_str = f"-{number_str}"

    if symbol_position == "before":
        return f"{symbol}{number_str}"
    return f"{number_str} {symbol}"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_currency(value: str) -> Decimal:
    """Parse a human-readable currency string into a ``Decimal``.

    Strips common currency symbols, whitespace, and thousands separators
    (commas) before parsing.

    Args:
        value: String such as ``"$1,234.56"``, ``"1 234.56 €"``,
            ``"-£99.99"``, or plain ``"42.5"``.

    Returns:
        ``Decimal`` representation of the numeric value.

    Raises:
        ValueError: If the string cannot be parsed as a number.

    Example::

        >>> parse_currency("$1,234.56")
        Decimal('1234.56')
        >>> parse_currency("-£99.99")
        Decimal('-99.99')
    """
    # Remove currency symbols and whitespace; keep digits, minus, dot
    cleaned = re.sub(r"[^\d.\-]", "", value.strip())
    if not cleaned or cleaned in ("-", "."):
        raise ValueError(f"Cannot parse {value!r} as a currency amount.")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Cannot parse {value!r} as a currency amount: {exc}") from exc


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


def convert_currency(
    amount: Decimal,
    rate: Decimal,
    *,
    decimal_places: int = 2,
) -> Decimal:
    """Apply an exchange *rate* to *amount* and round the result.

    Args:
        amount: Source amount.
        rate: Exchange rate (target / source).
        decimal_places: Precision of the result (default: 2).

    Returns:
        Converted and rounded ``Decimal``.

    Raises:
        ValueError: If *rate* is not positive.

    Example::

        >>> convert_currency(Decimal("100"), Decimal("1.08"))
        Decimal('108.00')
    """
    if rate <= 0:
        raise ValueError(f"Exchange rate must be positive, got {rate}")
    return round_currency(amount * rate, decimal_places)
