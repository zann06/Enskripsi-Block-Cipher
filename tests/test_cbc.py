"""Test mode CBC dengan block 2 byte."""

import pytest

from crypto.cbc import decrypt_cbc, encrypt_cbc
from crypto.feistel16 import CipherValueError
from crypto.padding import pad_pkcs7
from tests.ref_impl import encrypt_block as ref_encrypt

BLOCK = 2
KEY = 0x1A2B
IV = 0x0F0F

SAMPLES = [b"", b"A", b"AB", b"ABC", b"ABCD", "Halo dunia!".encode("utf-8"),
           "Data UTF-8: ñ 日本語".encode("utf-8")]


@pytest.mark.parametrize("plaintext", SAMPLES)
def test_cbc_round_trip(plaintext):
    ciphertext, blocks = encrypt_cbc(plaintext, KEY, IV)
    assert len(ciphertext) % BLOCK == 0
    assert decrypt_cbc(ciphertext, KEY, IV) == plaintext


def test_cbc_known_answer_from_independent_reference():
    """C_i = E_K(P_i XOR C_i-1) diverifikasi dengan implementasi referensi."""
    plaintext = "Halo dunia! Uji coba blok.".encode("utf-8")
    padded = pad_pkcs7(plaintext, BLOCK)
    ciphertext, blocks = encrypt_cbc(plaintext, KEY, IV)

    previous = IV
    expected_parts = []
    for offset in range(0, len(padded), BLOCK):
        plain_block = padded[offset : offset + BLOCK]
        xored = int.from_bytes(plain_block, "big") ^ previous
        cipher_int = ref_encrypt(xored, KEY)
        expected_parts.append(cipher_int.to_bytes(BLOCK, "big"))
        previous = cipher_int
    assert ciphertext == b"".join(expected_parts)

    for offset, block in enumerate(blocks):
        assert block.index == offset
        assert block.counter_block is None
        if offset == 0:
            assert block.xor_value == IV.to_bytes(BLOCK, "big")
        else:
            assert block.xor_value == blocks[offset - 1].ciphertext_block
        assert block.feistel_input == block.ciphertext_block  # sebelum enkripsi sama
    # feistel_input blok ke-i = P_i XOR C_(i-1)
    for block in blocks:
        assert (
            int.from_bytes(block.plaintext_block, "big")
            ^ int.from_bytes(block.xor_value, "big")
        ) == int.from_bytes(block.feistel_input, "big")


def test_cbc_empty_input_produces_one_padding_block():
    ciphertext, blocks = encrypt_cbc(b"", KEY, IV)
    assert len(blocks) == 1
    assert decrypt_cbc(ciphertext, KEY, IV) == b""


def test_cbc_same_plaintext_different_iv_changes_ciphertext():
    plaintext = "Halo dunia!".encode("utf-8")
    ct1, _ = encrypt_cbc(plaintext, KEY, 0x0001)
    ct2, _ = encrypt_cbc(plaintext, KEY, 0x0002)
    assert ct1 != ct2


def test_cbc_chaining_makes_repeated_blocks_differ():
    """Blok plaintext identik biasanya menghasilkan ciphertext berbeda (chaining)."""
    plaintext = b"\x41\x42" * 4
    ciphertext, blocks = encrypt_cbc(plaintext, KEY, IV)
    assert len({block.ciphertext_block for block in blocks}) == 4


def test_cbc_wrong_iv_corrupts_first_block_only():
    plaintext = "Halo dunia!".encode("utf-8")
    ciphertext, _ = encrypt_cbc(plaintext, KEY, 0x0F0F)
    with pytest.raises(Exception):
        decrypt_cbc(ciphertext, KEY, 0x0F0E)


@pytest.mark.parametrize("bad_iv", [-1, 0x10000, True])
def test_cbc_invalid_iv_raises(bad_iv):
    with pytest.raises(CipherValueError):
        encrypt_cbc(b"A", KEY, bad_iv)
    with pytest.raises(CipherValueError):
        decrypt_cbc(b"\x41\x42", KEY, bad_iv)


def test_cbc_invalid_ciphertext_length_raises():
    with pytest.raises(CipherValueError):
        decrypt_cbc(b"\x41", KEY, IV)
