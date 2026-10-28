"""Encoding and formatting helpers shared by the UI and PDF report."""

from __future__ import annotations

import re

from .feistel16 import BLOCK_BITS, BLOCK_BYTES, MAX_BLOCK, MAX_KEY, CipherValueError


def parse_hex16(value: str, label: str = "Nilai") -> int:
    """Parse a 16-bit value written as hexadecimal.

    ``0x`` is optional and underscores/spaces are ignored. Four hex digits are
    recommended, but shorter values are accepted (``A`` == ``0x000A``).
    """
    raw = str(value).strip().replace("_", "").replace(" ", "")
    if raw.lower().startswith("0x"):
        raw = raw[2:]
    if not raw:
        raise CipherValueError(f"{label} wajib diisi (HEX 16-bit, contoh: 1A2B).")
    if not re.fullmatch(r"[0-9A-Fa-f]{1,4}", raw):
        raise CipherValueError(
            f"{label} harus berupa HEX 16-bit (0x0000–0xFFFF), contoh: 1A2B."
        )
    parsed = int(raw, 16)
    if not 0 <= parsed <= 0xFFFF:
        raise CipherValueError(f"{label} harus berada pada rentang 0x0000–0xFFFF.")
    return parsed


def parse_key(value: str) -> int:
    return parse_hex16(value, "Kunci")


def parse_iv(value: str) -> int:
    return parse_hex16(value, "IV")


def parse_counter(value: str) -> int:
    return parse_hex16(value, "Counter awal")


def int16_to_hex(value: int) -> str:
    return f"{value:04X}"


def int16_to_bin(value: int) -> str:
    return f"{value:016b}"


def format_hex(data: bytes) -> str:
    """Uppercase hex with one space between bytes (``4F A2``)."""
    return " ".join(f"{byte:02X}" for byte in data)


def format_bin(data: bytes) -> str:
    """Binary per byte, separated by one space (``01001111 10100010``)."""
    return " ".join(f"{byte:08b}" for byte in data)


def text_to_bytes(text: str) -> bytes:
    """Encode user text as UTF-8 without silently changing it."""
    return text.encode("utf-8")


def bytes_to_text(data: bytes) -> str:
    """Decode UTF-8, raising a helpful error for invalid byte sequences."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Hasil dekripsi bukan UTF-8 yang valid; periksa kunci, IV, atau counter."
        ) from exc


def display_text(text: str, limit: int | None = None) -> str:
    """Return text with control characters escaped for table display."""
    rendered = text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    if limit is not None and len(rendered) > limit:
        return rendered[:limit] + "…"
    return rendered


__all__ = [
    "BLOCK_BITS",
    "BLOCK_BYTES",
    "MAX_BLOCK",
    "MAX_KEY",
    "parse_hex16",
    "parse_key",
    "parse_iv",
    "parse_counter",
    "int16_to_hex",
    "int16_to_bin",
    "format_hex",
    "format_bin",
    "text_to_bytes",
    "bytes_to_text",
    "display_text",
]
