"""Toy 16-bit Feistel network used by CipherLab.

The cipher is intentionally small and simple so every step can be inspected in
the UI and in a report. It is **not** a secure cipher, is **not** AES, and must
not be used for real data.

Specification
-------------
* Block size: 16 bit (2 byte), split into two 8-bit halves ``L`` and ``R``.
* Key size: 16 bit.
* Rounds: 8.
* Round function: ``F(R, k) = ROTL8(SBOX[R XOR k], 1)``.
* Round: ``(L, R) <- (R, L XOR F(R, k_i))``.
* Key schedule: for round ``i`` (0..7), rotate the 16-bit key left by ``3*i``
  bits, split into high/low bytes, XOR each with the round constant, pass
  through S-box, rotate low-byte result by ``(index % 7) + 1`` bits, then
  XOR the two results to produce the 8-bit round key.
* No final swap is applied. Decryption runs the rounds in reverse with the
  equivalent inverse update ``(L, R) <- (R XOR F(L, k_i), L)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

BLOCK_BITS = 16
BLOCK_BYTES = 2
ROUNDS = 8
KEY_BITS = 16
MAX_BLOCK = (1 << BLOCK_BITS) - 1
MAX_KEY = (1 << KEY_BITS) - 1

# A fixed 256-byte permutation. It is part of the algorithm specification so
# that results are reproducible across machines and Python versions.
SBOX: tuple[int, ...] = (
    0x77, 0xD3, 0x2D, 0x08, 0xB1, 0xFE, 0x52, 0x4C, 0x2E, 0x98, 0x69, 0x8D, 0x9F, 0xBD, 0xB4, 0x80,
    0xB0, 0x76, 0xF5, 0x4E, 0x00, 0x11, 0xEB, 0x83, 0xCA, 0x2F, 0xEC, 0x9C, 0xD7, 0x7D, 0x6A, 0xA6,
    0x53, 0x12, 0xF7, 0x36, 0x26, 0x45, 0x46, 0x5C, 0xC0, 0x61, 0x82, 0xB9, 0x5D, 0x0B, 0xC9, 0x19,
    0xFA, 0x88, 0x1D, 0xA1, 0x17, 0x09, 0x15, 0xA9, 0xE1, 0x7E, 0xB3, 0x07, 0x67, 0x8B, 0x3D, 0xB7,
    0x7F, 0x6E, 0x13, 0x05, 0x27, 0x1E, 0x78, 0x5B, 0xDF, 0x16, 0xF6, 0x04, 0x28, 0x6C, 0x03, 0xE4,
    0xD4, 0x85, 0xE2, 0xD5, 0x30, 0x2C, 0x62, 0x14, 0x20, 0x8E, 0x7C, 0x4D, 0x8C, 0x6D, 0x59, 0xF2,
    0xA7, 0x37, 0xC6, 0x54, 0x3A, 0xE3, 0x89, 0xBC, 0x8F, 0x2A, 0x71, 0x2B, 0xAE, 0xBA, 0xED, 0x66,
    0x23, 0x49, 0x8A, 0xE8, 0x79, 0x96, 0x01, 0x10, 0xCF, 0x41, 0x60, 0xB5, 0xF9, 0x1F, 0xD6, 0x90,
    0x4B, 0x4A, 0x87, 0xAC, 0xE9, 0x97, 0x22, 0x5E, 0x57, 0x44, 0x25, 0xAF, 0xC2, 0xCD, 0xF8, 0xD9,
    0x18, 0x9B, 0xA8, 0x70, 0x86, 0x92, 0x29, 0x06, 0xDB, 0x84, 0xFB, 0x34, 0x7A, 0xF4, 0x33, 0x0F,
    0x73, 0xC5, 0xB8, 0xC4, 0xDE, 0x50, 0xDC, 0xEA, 0xF0, 0xE5, 0x3F, 0x56, 0x91, 0x1A, 0xFF, 0xB6,
    0x75, 0x93, 0x43, 0xD2, 0x02, 0x72, 0x35, 0x81, 0x21, 0xEE, 0xB2, 0x3B, 0x6F, 0x0A, 0x1B, 0x64,
    0xAB, 0x3C, 0xAD, 0xF1, 0xD8, 0x5A, 0x51, 0x63, 0x1C, 0x31, 0x0D, 0xAA, 0xC7, 0x9A, 0xBE, 0xA0,
    0x40, 0x5F, 0x0C, 0x3E, 0xA5, 0xCC, 0xF3, 0x24, 0x47, 0xC1, 0x42, 0xBF, 0xCB, 0xE7, 0xEF, 0x0E,
    0xD0, 0x39, 0x55, 0x9E, 0x74, 0xE6, 0x65, 0x99, 0xA3, 0xA2, 0x94, 0xFC, 0xBB, 0xE0, 0x38, 0x58,
    0xCE, 0xC3, 0xC8, 0xFD, 0x4F, 0x7B, 0xA4, 0x6B, 0xD1, 0xDD, 0x95, 0x32, 0x68, 0x9D, 0xDA, 0x48,
)

ROUND_CONSTANTS: tuple[int, ...] = (
    0x9E, 0xB9, 0xD4, 0xEF, 0x0A, 0x25, 0x40, 0x5B,
)


class CipherValueError(ValueError):
    """Raised when a block, key, IV, or counter is outside the 16-bit range."""


@dataclass(frozen=True)
class RoundTrace:
    """One Feistel round, captured exactly as it was computed."""

    round_index: int
    left_in: int
    right_in: int
    round_key: int
    f_output: int
    left_out: int
    right_out: int

    @property
    def round_number(self) -> int:
        """Human-friendly 1-based round number."""
        return self.round_index + 1


def validate_int16(value: int, label: str = "nilai") -> int:
    """Validate that *value* is an integer in the 16-bit range."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise CipherValueError(f"{label} harus berupa bilangan bulat 16-bit.")
    if not 0 <= value <= MAX_BLOCK:
        raise CipherValueError(f"{label} harus berada pada rentang 0x0000–0xFFFF.")
    return value


def _rotl8(value: int, shift: int) -> int:
    shift %= 8
    if shift == 0:
        return value & 0xFF
    return ((value << shift) | (value >> (8 - shift))) & 0xFF


def _rotl16(value: int, shift: int) -> int:
    shift %= 16
    if shift == 0:
        return value & 0xFFFF
    return ((value << shift) | (value >> (16 - shift))) & 0xFFFF


def round_function(right: int, round_key: int) -> int:
    """The documented round function ``F(R, k)``."""
    return _rotl8(SBOX[(right ^ round_key) & 0xFF], 1)


def key_schedule(key: int) -> tuple[int, ...]:
    """Expand a 16-bit key into eight 8-bit round keys.

    Matching the reference specification exactly: rotate left 3*i bits, split
    high/low bytes, XOR each with the round constant, pass through S-box, rotate
    low-byte result by (index % 7) + 1 bits, then XOR the two results.
    """
    validate_int16(key, "Kunci")
    round_keys: list[int] = []
    for index in range(ROUNDS):
        rotated = _rotl16(key, 3 * index)
        high = (rotated >> 8) & 0xFF
        low = rotated & 0xFF
        high_mix = SBOX[high ^ ROUND_CONSTANTS[index]]
        low_mix = _rotl8(SBOX[low ^ ((ROUND_CONSTANTS[index] << 1) & 0xFF)], (index % 7) + 1)
        round_keys.append(high_mix ^ low_mix)
    return tuple(round_keys)


def encrypt_block(block: int, key: int, collect_trace: bool = False):
    """Encrypt one 16-bit block.

    Returns the ciphertext integer, or ``(ciphertext, rounds)`` when
    *collect_trace* is true.
    """
    validate_int16(block, "Blok")
    validate_int16(key, "Kunci")
    left = (block >> 8) & 0xFF
    right = block & 0xFF
    traces: list[RoundTrace] = []
    round_keys = key_schedule(key)

    for index, round_key in enumerate(round_keys):
        left_in, right_in = left, right
        f_output = round_function(right_in, round_key)
        left, right = right_in, left_in ^ f_output
        if collect_trace:
            traces.append(
                RoundTrace(
                    round_index=index,
                    left_in=left_in,
                    right_in=right_in,
                    round_key=round_key,
                    f_output=f_output,
                    left_out=left,
                    right_out=right,
                )
            )

    result = ((left << 8) | right) & 0xFFFF
    if collect_trace:
        return result, traces
    return result


def decrypt_block(block: int, key: int, collect_trace: bool = False):
    """Decrypt one 16-bit block (inverse of :func:`encrypt_block`)."""
    validate_int16(block, "Blok")
    validate_int16(key, "Kunci")
    left = (block >> 8) & 0xFF
    right = block & 0xFF
    traces: list[RoundTrace] = []
    round_keys = key_schedule(key)

    for index in range(ROUNDS - 1, -1, -1):
        round_key = round_keys[index]
        left_in, right_in = left, right
        f_output = round_function(left_in, round_key)
        left, right = right_in ^ f_output, left_in
        if collect_trace:
            traces.append(
                RoundTrace(
                    round_index=index,
                    left_in=left_in,
                    right_in=right_in,
                    round_key=round_key,
                    f_output=f_output,
                    left_out=left,
                    right_out=right,
                )
            )

    result = ((left << 8) | right) & 0xFFFF
    if collect_trace:
        return result, traces
    return result


def bytes_to_block(data: bytes, label: str = "Blok") -> int:
    """Convert exactly two bytes (big-endian) to a 16-bit integer."""
    if len(data) != BLOCK_BYTES:
        raise CipherValueError(f"{label} harus tepat {BLOCK_BYTES} byte (16 bit).")
    return int.from_bytes(data, "big")


def block_to_bytes(value: int) -> bytes:
    """Convert a 16-bit integer to exactly two bytes (big-endian)."""
    return validate_int16(value, "Blok").to_bytes(BLOCK_BYTES, "big")


def xor_blocks(left: bytes, right: bytes) -> bytes:
    """XOR two equally sized byte strings (1–2 bytes are expected here)."""
    if len(left) != len(right):
        raise ValueError("Panjang blok XOR harus sama.")
    return bytes(a ^ b for a, b in zip(left, right))


def format_round_traces(traces: Iterable[RoundTrace]) -> list[dict[str, str]]:
    """Format round traces for display (all values are actual trace values)."""
    return [
        {
            "Ronde": str(trace.round_number),
            "L masuk": f"{trace.left_in:02X}",
            "R masuk": f"{trace.right_in:02X}",
            "K ronde": f"{trace.round_key:02X}",
            "F(R, K)": f"{trace.f_output:02X}",
            "L keluar": f"{trace.left_out:02X}",
            "R keluar": f"{trace.right_out:02X}",
        }
        for trace in traces
    ]