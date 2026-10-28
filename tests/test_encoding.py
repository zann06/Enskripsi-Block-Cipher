"""Test helper encoding/parsing HEX dan teks."""

import pytest

from crypto.encoding import (
    bytes_to_text,
    display_text,
    format_bin,
    format_hex,
    int16_to_bin,
    int16_to_hex,
    parse_counter,
    parse_hex16,
    parse_iv,
    parse_key,
    text_to_bytes,
)
from crypto.feistel16 import CipherValueError


@pytest.mark.parametrize("raw,expected", [
    ("1A2B", 0x1A2B),
    ("0x1A2B", 0x1A2B),
    ("abcd", 0xABCD),
    ("A", 0x000A),
    ("1_2", 0x0012),
    (" 0F 0F ", 0x0F0F),
    ("0000", 0x0000),
    ("FFFF", 0xFFFF),
])
def test_parse_hex16_valid(raw, expected):
    assert parse_hex16(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "GGGG", "12345", "0x", "12G4", "XYZ", "0x12345", "-1"])
def test_parse_hex16_invalid_raises(raw):
    with pytest.raises(CipherValueError):
        parse_hex16(raw)


def test_parse_aliases():
    assert parse_key("1A2B") == 0x1A2B
    assert parse_iv("0F0F") == 0x0F0F
    assert parse_counter("00C8") == 0x00C8


def test_formatters():
    assert int16_to_hex(0x1A2B) == "1A2B"
    assert int16_to_bin(0x1A2B) == "0001101000101011"
    assert format_hex(b"\x4f\xa2") == "4F A2"
    assert format_bin(b"\x4f\xa2") == "01001111 10100010"
    assert format_hex(b"") == ""
    assert format_bin(b"") == ""


def test_text_bytes_round_trip_utf8():
    for text in ("", "Halo dunia!", "ñ 日本語", "emoji 🔐", "baris\nbaru\ttab"):
        assert bytes_to_text(text_to_bytes(text)) == text


def test_bytes_to_text_invalid_raises():
    with pytest.raises(ValueError, match="UTF-8"):
        bytes_to_text(b"\xff\xfe\xfa")


def test_display_text_escapes_control_chars():
    assert display_text("a\nb\tc\rd") == "a\\nb\\tc\\rd"


def test_display_text_limit_marks_truncation():
    result = display_text("x" * 50, limit=10)
    assert result.startswith("xxxxxxxxxx")
    assert result.endswith("…")
