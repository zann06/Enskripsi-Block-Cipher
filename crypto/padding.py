"""PKCS#7 padding adapted to CipherLab's 2-byte block size."""

from __future__ import annotations

BLOCK_SIZE = 2


class PaddingError(ValueError):
    """Raised when PKCS#7 padding is missing, malformed, or inconsistent."""


def pad_pkcs7(data: bytes, block_size: int = BLOCK_SIZE) -> bytes:
    """Append PKCS#7 padding, always adding 1..block_size bytes.

    Empty input becomes one full block (``b"\\x02\\x02"`` for a 2-byte block),
    so ECB/CBC always produce at least one ciphertext block.
    """
    if block_size < 1 or block_size > 255:
        raise ValueError("Ukuran blok padding harus antara 1 dan 255 byte.")
    pad_length = block_size - (len(data) % block_size)
    return data + bytes([pad_length]) * pad_length


def unpad_pkcs7(data: bytes, block_size: int = BLOCK_SIZE) -> bytes:
    """Validate and remove PKCS#7 padding.

    Raises :class:`PaddingError` for empty data, a non-multiple length, an
    out-of-range pad byte, or mismatched padding bytes.
    """
    if block_size < 1 or block_size > 255:
        raise ValueError("Ukuran blok padding harus antara 1 dan 255 byte.")
    if not data:
        raise PaddingError("Data kosong tidak memiliki padding PKCS#7 yang valid.")
    if len(data) % block_size != 0:
        raise PaddingError(
            f"Panjang data ({len(data)} byte) bukan kelipatan ukuran blok ({block_size} byte)."
        )

    pad_length = data[-1]
    if pad_length < 1 or pad_length > block_size:
        raise PaddingError(
            f"Nilai padding {pad_length} tidak valid untuk ukuran blok {block_size} byte."
        )
    if data[-pad_length:] != bytes([pad_length]) * pad_length:
        raise PaddingError("Byte padding PKCS#7 tidak konsisten.")
    return data[:-pad_length]
