"""Test cipher inti Feistel 16-bit.

Termasuk known-answer test independen (``tests/ref_impl.py`` ditulis ulang
dari spesifikasi) dan pengujian invers ekshaustif atas seluruh 65.536 blok
untuk beberapa kunci uji.
"""

import pytest

from crypto.feistel16 import (
    BLOCK_BITS,
    ROUNDS,
    CipherValueError,
    decrypt_block,
    encrypt_block,
    format_round_traces,
    key_schedule,
    round_function,
)
from tests import ref_impl

# Vektor known-answer beku, dihitung dengan tests/ref_impl.py (implementasi
# independen dari spesifikasi terdokumentasi) dan diverifikasi manual.
KAT_VECTORS = [
    # (plaintext block, key, expected ciphertext)
    (0x0123, 0x4567, 0x706F),
    (0xFFFF, 0x0000, 0xEA51),
    (0x0000, 0xFFFF, 0x99DF),
    (0xA5A5, 0x1A2B, 0xDC81),
    (0x0001, 0x0001, 0x9EAC),
]


@pytest.mark.parametrize("block,key,expected", KAT_VECTORS)
def test_known_answer_encrypt(block, key, expected):
    """Known-answer test: ciphertext harus sama dengan vektor independen."""
    assert encrypt_block(block, key) == expected


@pytest.mark.parametrize("block,key,expected", KAT_VECTORS)
def test_known_answer_decrypt(block, key, expected):
    assert decrypt_block(expected, key) == block


@pytest.mark.parametrize("block,key", [(b, k) for b, k, _ in KAT_VECTORS])
def test_matches_independent_reference(block, key):
    """Ciphertext implementasi == hasil implementasi referensi independen."""
    assert encrypt_block(block, key) == ref_impl.encrypt_block(block, key)


@pytest.mark.parametrize("key", [0x0000, 0x1A2B, 0xBEEF, 0xFFFF])
def test_inverse_exhaustive_all_65536_blocks(key):
    """decrypt_block(encrypt_block(x)) == x untuk SELURUH blok 16-bit."""
    for block in range(1 << BLOCK_BITS):
        assert decrypt_block(encrypt_block(block, key), key) == block


def test_encrypt_is_not_identity_or_xor_key():
    """Sanity: cipher tidak boleh collapse menjadi XOR biasa."""
    for block in (0x0000, 0x1111, 0x8000, 0xFFFF):
        for key in (0x0000, 0x5A5A, 0xFFFF):
            assert encrypt_block(block, key) != (block ^ key)
            assert encrypt_block(block, key) != block


def test_round_function_documented_formula():
    for right in (0x00, 0x01, 0x80, 0xFF):
        for round_key in (0x00, 0x42, 0xFF):
            sboxed = ref_impl.SBOX[right ^ round_key]
            expected = ((sboxed << 1) | (sboxed >> 7)) & 0xFF
            assert round_function(right, round_key) == expected


def test_key_schedule_deterministic_and_in_range():
    first = key_schedule(0x1A2B)
    second = key_schedule(0x1A2B)
    assert first == second
    assert len(first) == ROUNDS
    assert all(0 <= rk <= 0xFF for rk in first)
    assert [f"0x{rk:02X}" for rk in first] == [
        "0xEE", "0x85", "0x36", "0xA7", "0x9D", "0x4C", "0x6E", "0xF3",
    ]


def test_key_schedule_matches_reference():
    for key in (0x0000, 0x1A2B, 0xFFFF):
        assert list(key_schedule(key)) == ref_impl.round_keys(key)


def test_key_schedule_varies_by_key():
    schedules = {key_schedule(key) for key in (0x0000, 0x0001, 0x0100, 0xFFFF, 0xA5A5)}
    assert len(schedules) == 5


def test_trace_matches_recomputation():
    ciphertext, traces = encrypt_block(0x0123, 0x4567, collect_trace=True)
    assert len(traces) == ROUNDS
    left, right = 0x01, 0x23
    for trace in traces:
        assert trace.left_in == left and trace.right_in == right
        assert trace.f_output == round_function(right, trace.round_key)
        left, right = right, left ^ trace.f_output
        assert (trace.left_out, trace.right_out) == (left, right)
    assert ((left << 8) | right) == ciphertext
    formatted = format_round_traces(traces)
    assert formatted[0]["Ronde"] == "1" and formatted[-1]["Ronde"] == str(ROUNDS)


@pytest.mark.parametrize("bad", [-1, 0x10000, 65536, True, 1.5, "1A2B", None])
def test_invalid_block_or_key_raises(bad):
    if bad is True:
        # bool adalah int di Python; implementasi menolaknya secara eksplisit
        with pytest.raises(CipherValueError):
            encrypt_block(0x1234, bad)
    elif isinstance(bad, (int, float)):
        with pytest.raises(CipherValueError):
            encrypt_block(bad, 0x1234)
        with pytest.raises(CipherValueError):
            encrypt_block(0x1234, bad)
    else:
        with pytest.raises(CipherValueError):
            encrypt_block(0x1234, bad)
