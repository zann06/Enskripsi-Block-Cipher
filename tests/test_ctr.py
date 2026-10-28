"""Test mode CTR dengan block 2 byte, termasuk overflow counter."""

import pytest

from crypto.ctr import COUNTER_LIMIT, CounterOverflowError, decrypt_ctr, encrypt_ctr
from crypto.feistel16 import CipherValueError, encrypt_block
from tests.ref_impl import encrypt_block as ref_encrypt

BLOCK = 2
KEY = 0x1A2B
COUNTER = 0x00C8

SAMPLES = [b"", b"A", b"AB", b"ABC", b"ABCD", "Halo dunia!".encode("utf-8"),
           "Data UTF-8: ñ 日本語".encode("utf-8")]


@pytest.mark.parametrize("plaintext", SAMPLES)
def test_ctr_round_trip(plaintext):
    ciphertext, blocks = encrypt_ctr(plaintext, KEY, COUNTER)
    assert len(ciphertext) == len(plaintext)  # CTR mempertahankan panjang
    assert decrypt_ctr(ciphertext, KEY, COUNTER) == plaintext


def test_ctr_known_answer_from_independent_reference():
    """C_i = P_i XOR E_K(T_i) diverifikasi dengan implementasi referensi."""
    plaintext = "Halo dunia! Uji coba blok.".encode("utf-8")
    ciphertext, blocks = encrypt_ctr(plaintext, KEY, COUNTER)

    expected = bytearray()
    for index, offset in enumerate(range(0, len(plaintext), BLOCK)):
        counter = COUNTER + index
        stream = ref_encrypt(counter, KEY).to_bytes(BLOCK, "big")
        expected.extend(a ^ b for a, b in zip(plaintext[offset : offset + BLOCK], stream))
    assert ciphertext == bytes(expected)

    for index, block in enumerate(blocks):
        assert block.counter_block == (COUNTER + index).to_bytes(BLOCK, "big")
        assert block.keystream == ref_encrypt(COUNTER + index, KEY).to_bytes(BLOCK, "big")
        assert block.xor_value == block.keystream
        assert (
            int.from_bytes(block.plaintext_block, "big")
            ^ int.from_bytes(block.keystream, "big")
        ) == int.from_bytes(block.ciphertext_block, "big")
        assert len(block.feistel_rounds) == 8


def test_ctr_empty_plaintext_has_no_blocks():
    ciphertext, blocks = encrypt_ctr(b"", KEY, COUNTER)
    assert ciphertext == b"" and blocks == []
    assert decrypt_ctr(b"", KEY, COUNTER) == b""


def test_ctr_partial_last_block():
    plaintext = b"\x41\x42\x43"  # 1 blok penuh + 1 byte parsial
    ciphertext, blocks = encrypt_ctr(plaintext, KEY, COUNTER)
    assert len(blocks) == 2
    assert len(blocks[-1].plaintext_block) == 1
    assert len(blocks[-1].ciphertext_block) == 1
    assert decrypt_ctr(ciphertext, KEY, COUNTER) == plaintext


def test_ctr_keystream_independent_of_plaintext():
    """Keystream hanya bergantung pada counter dan kunci."""
    _, blocks1 = encrypt_ctr(b"\x00\x00\x00", KEY, COUNTER)
    _, blocks2 = encrypt_ctr(b"\xFF\xFF\xFF", KEY, COUNTER)
    assert [b.keystream for b in blocks1] == [b.keystream for b in blocks2]


@pytest.mark.parametrize("counter,blocks_used,overflow", [
    (0x0000, 3, False),
    (0xFFFD, 3, False),   # blok terakhir tepat 0xFFFF
    (0xFFFE, 2, False),
    (0xFFFF, 1, False),   # hanya satu blok
    (0xFFFE, 3, True),    # 0xFFFE, 0xFFFF, lalu 0x10000 -> overflow
    (0xFFFF, 2, True),
    (0xFFF0, 17, True),
])
def test_counter_overflow_boundary(counter, blocks_used, overflow):
    plaintext = bytes(blocks_used * BLOCK) if not overflow else bytes((blocks_used - 1) * BLOCK + 1)
    if overflow:
        with pytest.raises(CounterOverflowError):
            encrypt_ctr(plaintext, KEY, counter)
    else:
        ciphertext, _ = encrypt_ctr(plaintext, KEY, counter)
        assert decrypt_ctr(ciphertext, KEY, counter) == plaintext


def test_counter_overflow_message_mentions_limit():
    with pytest.raises(CounterOverflowError, match="0xFFFF"):
        encrypt_ctr(bytes(6), KEY, 0xFFFC)


def test_decrypt_same_counter_limit():
    ciphertext, _ = encrypt_ctr(bytes(2), KEY, COUNTER_LIMIT)
    assert decrypt_ctr(ciphertext, KEY, COUNTER_LIMIT) == bytes(2)


@pytest.mark.parametrize("bad_counter", [-1, 0x10000, True])
def test_ctr_invalid_counter_raises(bad_counter):
    with pytest.raises(CipherValueError):
        encrypt_ctr(b"A", KEY, bad_counter)
    with pytest.raises(CipherValueError):
        decrypt_ctr(b"\x41", KEY, bad_counter)
