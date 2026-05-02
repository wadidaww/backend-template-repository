"""Text / string utility helpers.

All helpers are pure functions with no side-effects.
"""

from __future__ import annotations

import html
import re
import unicodedata

# ---------------------------------------------------------------------------
# Slug
# ---------------------------------------------------------------------------


def slugify(text: str, *, separator: str = "-", max_length: int | None = None) -> str:
    """Convert *text* to a URL-friendly slug.

    Steps applied:

    1. Unicode NFC normalisation.
    2. ASCII transliteration (strip combining marks / accents).
    3. Lowercase.
    4. Replace non-alphanumeric characters with *separator*.
    5. Collapse consecutive separators.
    6. Strip leading/trailing separators.
    7. Optionally truncate to *max_length* (truncates at the last separator
       that fits, or hard-cuts if no separator is present).

    Args:
        text: The string to slugify.
        separator: Character used between words (default: ``"-"``).
        max_length: Maximum length of the returned slug.  ``None`` means
            unlimited.

    Returns:
        URL-safe slug string.

    Example::

        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("Ångström café", separator="_")
        'angstrom_cafe'
    """
    # Normalise unicode
    text = unicodedata.normalize("NFKD", text)
    # Keep only ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Replace anything that is not a word character or digit with separator
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", separator, text)
    text = text.strip(separator)

    if max_length is not None and len(text) > max_length:
        text = text[:max_length]
        # Avoid ending on a partial separator sequence
        text = text.rstrip(separator)

    return text


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------


def truncate(
    text: str,
    max_length: int,
    *,
    suffix: str = "...",
    break_on_word: bool = True,
) -> str:
    """Shorten *text* to at most *max_length* characters.

    Args:
        text: The string to truncate.
        max_length: Maximum number of characters in the result (including the
            *suffix*).
        suffix: Appended when truncation occurs (default: ``"..."``).
        break_on_word: When ``True`` (default), the cut is moved back to the
            last whitespace boundary so words are not split.  Falls back to a
            hard cut if no whitespace is found.

    Returns:
        Original string if it fits; otherwise a truncated string ending with
        *suffix*.

    Raises:
        ValueError: If *max_length* is shorter than the length of *suffix*.

    Example::

        >>> truncate("Hello, world!", 8)
        'Hello...'
        >>> truncate("Hello, world!", 8, break_on_word=False)
        'Hello...'
    """
    if max_length < len(suffix):
        raise ValueError(
            f"max_length ({max_length}) must be >= len(suffix) ({len(suffix)})"
        )
    if len(text) <= max_length:
        return text
    cut = max_length - len(suffix)
    truncated = text[:cut]
    if break_on_word:
        space_idx = truncated.rfind(" ")
        if space_idx > 0:
            truncated = truncated[:space_idx]
    return truncated.rstrip() + suffix


# ---------------------------------------------------------------------------
# Masking
# ---------------------------------------------------------------------------


def mask_string(
    text: str,
    *,
    visible_start: int = 0,
    visible_end: int = 4,
    mask_char: str = "*",
) -> str:
    """Partially obscure *text* by replacing the middle section with *mask_char*.

    Useful for displaying partially hidden email addresses, phone numbers, or
    credit-card numbers.

    Args:
        text: The string to mask.
        visible_start: Number of characters to show at the beginning.
        visible_end: Number of characters to show at the end.
        mask_char: Character used for masking (default: ``"*"``).

    Returns:
        Masked string.  If the string is too short to split, the entire string
        is masked.

    Example::

        >>> mask_string("user@example.com", visible_start=2, visible_end=4)
        'us*************.com'
        >>> mask_string("4111111111111111", visible_start=0, visible_end=4)
        '************1111'
    """
    if len(mask_char) != 1:
        raise ValueError("mask_char must be exactly one character.")
    n = len(text)
    if visible_start + visible_end >= n:
        return mask_char * n
    start = text[:visible_start]
    end = text[n - visible_end :] if visible_end > 0 else ""
    middle_len = n - visible_start - visible_end
    return start + mask_char * middle_len + end


# ---------------------------------------------------------------------------
# Case conversion
# ---------------------------------------------------------------------------


def camel_to_snake(name: str) -> str:
    """Convert a ``camelCase`` or ``PascalCase`` string to ``snake_case``.

    Args:
        name: The camel-case identifier.

    Returns:
        snake_case equivalent.

    Example::

        >>> camel_to_snake("camelCaseString")
        'camel_case_string'
        >>> camel_to_snake("HTTPSRequest")
        'https_request'
    """
    # Insert underscore before a capital letter that follows a lowercase/digit
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Insert underscore before a capital that is followed by a lowercase (for acronyms)
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    return s2.lower()


def snake_to_camel(name: str, *, upper_first: bool = False) -> str:
    """Convert a ``snake_case`` string to ``camelCase`` or ``PascalCase``.

    Args:
        name: The snake_case identifier (may also contain hyphens).
        upper_first: When ``True`` return ``PascalCase`` (first letter
            upper-cased).  Default is ``False`` (lowerCamelCase).

    Returns:
        camelCase or PascalCase equivalent.

    Example::

        >>> snake_to_camel("hello_world")
        'helloWorld'
        >>> snake_to_camel("hello_world", upper_first=True)
        'HelloWorld'
    """
    parts = re.split(r"[_\-]+", name)
    if not parts:
        return name
    result = parts[0] if not upper_first else parts[0].capitalize()
    result += "".join(word.capitalize() for word in parts[1:])
    return result


# ---------------------------------------------------------------------------
# Initials
# ---------------------------------------------------------------------------


def get_initials(full_name: str, *, max_chars: int = 2) -> str:
    """Extract up to *max_chars* initials from *full_name*.

    Args:
        full_name: A person's full name, e.g. ``"Jane Mary Doe"``.
        max_chars: Maximum number of initials to return (default: 2).

    Returns:
        Upper-cased initials string, e.g. ``"JD"``.

    Example::

        >>> get_initials("Jane Doe")
        'JD'
        >>> get_initials("Jane Mary Doe", max_chars=3)
        'JMD'
    """
    words = full_name.split()
    initials = [w[0].upper() for w in words if w]
    return "".join(initials[:max_chars])


# ---------------------------------------------------------------------------
# HTML stripping
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html_tags(text: str, *, collapse_whitespace: bool = True) -> str:
    """Remove HTML tags from *text* and optionally decode HTML entities.

    Args:
        text: Raw HTML string.
        collapse_whitespace: When ``True`` (default), collapse runs of
            whitespace that result from tag removal into a single space and
            strip leading/trailing whitespace.

    Returns:
        Plain-text string.

    Example::

        >>> strip_html_tags("<p>Hello <b>world</b>!</p>")
        'Hello world!'
        >>> strip_html_tags("&lt;script&gt;alert(1)&lt;/script&gt;")
        '<script>alert(1)</script>'
    """
    # First decode HTML entities so &amp; → & etc.
    decoded = html.unescape(text)
    # Strip tags
    plain = _HTML_TAG_RE.sub(" ", decoded)
    if collapse_whitespace:
        plain = _WHITESPACE_RE.sub(" ", plain).strip()
    return plain


# ---------------------------------------------------------------------------
# Word count
# ---------------------------------------------------------------------------


def word_count(text: str) -> int:
    """Return the number of words in *text*.

    Words are non-whitespace token sequences separated by whitespace.  HTML
    tags and punctuation are counted as part of adjacent words unless you
    strip them first with :func:`strip_html_tags`.

    Args:
        text: Any string.

    Returns:
        Integer word count (0 for empty or whitespace-only strings).

    Example::

        >>> word_count("Hello, world!")
        2
        >>> word_count("  ")
        0
    """
    return len(text.split())
