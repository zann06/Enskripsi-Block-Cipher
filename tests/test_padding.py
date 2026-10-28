"""Test PKCS#7 padding dengan block size 2 byte."""

import pytest

from crypto.padding import PaddingError, pad_pkcs7, unpad_pkcs7

BLOCK_SIZE = 2


@pytest.mark.parametrize("length", list(range(0, 8)))
def test_pad_unpad_round_trip_all_lengths(length):
    data = bytes(range(length))
    padded = pad_pkcs7(data, BLOCK_SIZE)
    assert len(padded) % BLOCK_SIZE == 0
    assert unpad_pkcs7(padded, BLOCK_SIZE) == data


def test_empty_input_becomes_full_padding_block():
    assert pad_pkcs7(b"", BLOCK_SIZE) == b"\x02\x02"
    assert unpad_pkcs7(b"\x02\x02", BLOCK_SIZE) == b""


def test_exact_multiple_gets_full_pad_block():
    assert pad_pkcs7(b"\x41\x42", BLOCK_SIZE) == b"\x41\x42\x02\x02"


def test_odd_input_gets_one_pad_byte():
    assert pad_pkcs7(b"A", BLOCK_SIZE) == b"A\x01"
    assert unpad_pkcs7(b"A\x01", BLOCK_SIZE) == b"A"


@pytest.mark.parametrize(
    "data",
    [
        b"",                      # kosong tidak punya padding
        b"\x41",                  # panjang bukan kelipatan blok
        b"\x41\x42\x43",          # 3 byte, bukan kelipatan 2
        b"\x41\x00",              # nilai padding 0
        b"\x41\x03",              # nilai padding melebihi ukuran blok
        b"\x41\x02\x42\x01",      # byte padding tidak konsisten
        b"\x02\x01\x02\x01",      # pola inkonsisten lain
    ],
)
def test_unpad_invalid_raises(data):
    with pytest.raises(PaddingError):
        unpad_pkcs7(data, BLOCK_SIZE)


def test_pad_invalid_block_size_raises():
    for size in (0, 256, -1):
        with pytest.raises(ValueError):
            pad_pkcs7(b"A", size)
        with pytest.raises(ValueError):
            unpad_pkcs7(b"A\x01", size)
