"""Unit tests for app.utils.text."""

from __future__ import annotations

import pytest

from app.utils.text import (
    camel_to_snake,
    get_initials,
    mask_string,
    slugify,
    snake_to_camel,
    strip_html_tags,
    truncate,
    word_count,
)

# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_simple_words(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_accented_characters_transliterated(self):
        assert slugify("café") == "cafe"
        assert slugify("Ångström") == "angstrom"

    def test_custom_separator(self):
        assert slugify("Hello World", separator="_") == "hello_world"

    def test_max_length_truncates(self):
        result = slugify("hello world foo bar", max_length=10)
        assert len(result) <= 10

    def test_max_length_does_not_end_with_separator(self):
        result = slugify("hello world", max_length=8)
        assert not result.endswith("-")

    def test_numbers_preserved(self):
        assert slugify("Python 3.12 release") == "python-312-release"

    def test_consecutive_separators_collapsed(self):
        assert slugify("hello   world") == "hello-world"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_already_slug(self):
        assert slugify("already-a-slug") == "already-a-slug"


# ---------------------------------------------------------------------------
# truncate
# ---------------------------------------------------------------------------


class TestTruncate:
    def test_short_string_unchanged(self):
        assert truncate("Hello", 10) == "Hello"

    def test_exact_length_unchanged(self):
        assert truncate("Hello", 5) == "Hello"

    def test_truncates_at_word_boundary(self):
        result = truncate("Hello, world!", 8)
        assert result == "Hello..."

    def test_hard_cut_when_no_space(self):
        result = truncate("Superlongword", 10, break_on_word=False)
        assert result == "Superlo..."
        assert len(result) == 10

    def test_custom_suffix(self):
        # break_on_word=True walks back to the last space, landing after "Hello,"
        assert truncate("Hello, world!", 9, suffix="…") == "Hello,…"

    def test_break_on_word_false(self):
        result = truncate("Hello world", 7, break_on_word=False)
        assert result == "Hell..."

    def test_suffix_longer_than_max_raises(self):
        with pytest.raises(ValueError, match="max_length"):
            truncate("Hello", 2, suffix="...")

    def test_unicode_text(self):
        text = "日本語のテキスト"
        result = truncate(text, 5)
        assert len(result) <= 5


# ---------------------------------------------------------------------------
# mask_string
# ---------------------------------------------------------------------------


class TestMaskString:
    def test_mask_middle(self):
        assert (
            mask_string("4111111111111111", visible_start=0, visible_end=4)
            == "************1111"
        )

    def test_visible_start_and_end(self):
        result = mask_string("user@example.com", visible_start=2, visible_end=4)
        assert result.startswith("us")
        assert result.endswith(".com")
        assert "*" in result

    def test_short_string_fully_masked(self):
        # 4 chars, visible_start=2, visible_end=4 → 2+4=6 >= 4 → all masked
        assert mask_string("abcd", visible_start=2, visible_end=4) == "****"

    def test_custom_mask_char(self):
        result = mask_string("secret", visible_start=1, visible_end=1, mask_char="X")
        assert result == "sXXXXt"

    def test_zero_visible_end(self):
        result = mask_string("hello", visible_start=2, visible_end=0)
        assert result == "he***"

    def test_invalid_mask_char_raises(self):
        with pytest.raises(ValueError, match="mask_char"):
            mask_string("hello", mask_char="**")


# ---------------------------------------------------------------------------
# camel_to_snake
# ---------------------------------------------------------------------------


class TestCamelToSnake:
    def test_simple_camel(self):
        assert camel_to_snake("camelCase") == "camel_case"

    def test_pascal_case(self):
        assert camel_to_snake("PascalCase") == "pascal_case"

    def test_acronym(self):
        assert camel_to_snake("HTTPSRequest") == "https_request"

    def test_already_snake(self):
        assert camel_to_snake("already_snake") == "already_snake"

    def test_single_word(self):
        assert camel_to_snake("hello") == "hello"

    def test_multiple_capitals(self):
        assert camel_to_snake("myHTTPSConnection") == "my_https_connection"


# ---------------------------------------------------------------------------
# snake_to_camel
# ---------------------------------------------------------------------------


class TestSnakeToCamel:
    def test_basic(self):
        assert snake_to_camel("hello_world") == "helloWorld"

    def test_upper_first(self):
        assert snake_to_camel("hello_world", upper_first=True) == "HelloWorld"

    def test_single_word(self):
        assert snake_to_camel("hello") == "hello"

    def test_multiple_segments(self):
        assert snake_to_camel("one_two_three") == "oneTwoThree"

    def test_hyphen_separator(self):
        assert snake_to_camel("hello-world") == "helloWorld"

    def test_pascal_from_hyphen(self):
        assert snake_to_camel("my-component", upper_first=True) == "MyComponent"

    def test_roundtrip_with_camel_to_snake(self):
        original = "myVariableName"
        assert snake_to_camel(camel_to_snake(original)) == original


# ---------------------------------------------------------------------------
# get_initials
# ---------------------------------------------------------------------------


class TestGetInitials:
    def test_two_name(self):
        assert get_initials("Jane Doe") == "JD"

    def test_three_name_default_max(self):
        assert get_initials("Jane Mary Doe") == "JM"

    def test_three_name_max_three(self):
        assert get_initials("Jane Mary Doe", max_chars=3) == "JMD"

    def test_single_name(self):
        assert get_initials("Madonna") == "M"

    def test_extra_whitespace_ignored(self):
        assert get_initials("  Jane   Doe  ") == "JD"

    def test_empty_string(self):
        assert get_initials("") == ""

    def test_max_chars_zero(self):
        assert get_initials("Jane Doe", max_chars=0) == ""


# ---------------------------------------------------------------------------
# strip_html_tags
# ---------------------------------------------------------------------------


class TestStripHtmlTags:
    def test_simple_tags(self):
        assert strip_html_tags("<p>Hello <b>world</b>!</p>") == "Hello world !"

    def test_html_entities_decoded(self):
        # Entities are decoded first, then the resulting tags are stripped too.
        # &lt;script&gt;...&lt;/script&gt; → <script>...</script> → "alert(1)"
        assert strip_html_tags("&lt;script&gt;alert(1)&lt;/script&gt;") == "alert(1)"

    def test_html_entities_non_tag(self):
        # Entities that don't form tags survive as decoded text.
        assert strip_html_tags("&amp;hello&amp;") == "&hello&"

    def test_whitespace_collapsed(self):
        assert strip_html_tags("<p>  Hello   </p>") == "Hello"

    def test_no_collapse(self):
        result = strip_html_tags("<p>Hello</p>", collapse_whitespace=False)
        assert "Hello" in result

    def test_empty_string(self):
        assert strip_html_tags("") == ""

    def test_plain_text_unchanged(self):
        assert strip_html_tags("Hello world") == "Hello world"

    def test_self_closing_tag(self):
        result = strip_html_tags("Line1<br/>Line2")
        assert "Line1" in result
        assert "Line2" in result


# ---------------------------------------------------------------------------
# word_count
# ---------------------------------------------------------------------------


class TestWordCount:
    def test_simple_sentence(self):
        assert word_count("Hello, world!") == 2

    def test_empty_string(self):
        assert word_count("") == 0

    def test_whitespace_only(self):
        assert word_count("   ") == 0

    def test_single_word(self):
        assert word_count("Hello") == 1

    def test_multiple_spaces(self):
        assert word_count("one   two   three") == 3

    def test_newlines_count_as_separators(self):
        assert word_count("line one\nline two") == 4
