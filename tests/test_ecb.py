"""Test mode ECB dengan block 2 byte."""

import pytest

from crypto.ecb import decrypt_ecb, encrypt_ecb
from crypto.feistel16 import CipherValueError, encrypt_block
from crypto.padding import pad_pkcs7
from tests.ref_impl import encrypt_block as ref_encrypt

BLOCK = 2
KEY = 0x1A2B

SAMPLES = [b"", b"A", b"AB", b"ABC", b"ABCD", "Halo dunia!".encode("utf-8"),
           "Data UTF-8: ñ 日本語 ✅".encode("utf-8")]


@pytest.mark.parametrize("plaintext", SAMPLES)
def test_ecb_round_trip(plaintext):
    ciphertext, blocks = encrypt_ecb(plaintext, KEY)
    assert len(ciphertext) % BLOCK == 0
    assert len(blocks) == len(ciphertext) // BLOCK
    assert decrypt_ecb(ciphertext, KEY) == plaintext


def test_ecb_known_answer_from_independent_reference():
    """Setiap blok ECB harus sama dengan enkripsi blok referensi independen."""
    plaintext = "Halo dunia! Uji coba blok.".encode("utf-8")
    padded = pad_pkcs7(plaintext, BLOCK)
    ciphertext, blocks = encrypt_ecb(plaintext, KEY)
    expected = b"".join(
        ref_encrypt(int.from_bytes(padded[o : o + BLOCK], "big"), KEY).to_bytes(BLOCK, "big")
        for o in range(0, len(padded), BLOCK)
    )
    assert ciphertext == expected
    for offset, block in enumerate(blocks):
        assert block.index == offset
        assert block.plaintext_block == padded[offset * BLOCK : (offset + 1) * BLOCK]
        assert block.feistel_input == block.plaintext_block  # ECB tanpa XOR
        assert block.xor_value is None and block.counter_block is None
        assert len(block.feistel_rounds) == 8


def test_ecb_empty_input_produces_one_padding_block():
    ciphertext, blocks = encrypt_ecb(b"", KEY)
    assert len(blocks) == 1
    assert blocks[0].plaintext_block == b"\x02\x02"
    assert decrypt_ecb(ciphertext, KEY) == b""


def test_ecb_identical_blocks_produce_identical_ciphertext():
    """Karakteristik ECB, diverifikasi dari output aktual."""
    plaintext = b"\x41\x42" * 4  # 4 blok identik
    ciphertext, blocks = encrypt_ecb(plaintext, KEY)
    assert len({block.ciphertext_block for block in blocks}) == 1
    assert ciphertext == bytes(4 * blocks[0].ciphertext_block)


def test_ecb_collect_trace_false():
    ciphertext, blocks = encrypt_ecb(b"A", KEY, collect_trace=False)
    assert blocks[0].feistel_rounds == []


def test_ecb_invalid_ciphertext_length():
    with pytest.raises(CipherValueError):
        decrypt_ecb(b"\x41", KEY)  # 1 byte, bukan kelipatan 2


def test_ecb_invalid_key_raises():
    for bad_key in (-1, 0x10000):
        with pytest.raises(CipherValueError):
            encrypt_ecb(b"A", bad_key)
    with pytest.raises(CipherValueError):
        decrypt_ecb(b"\x41\x42", True)  # bool ditolak


def test_ecb_wrong_key_fails_padding_validation():
    ciphertext, _ = encrypt_ecb("Halo dunia!".encode("utf-8"), KEY)
    with pytest.raises(Exception):
        decrypt_ecb(ciphertext, 0xFFFF)  # hampir pasti padding tidak valid
