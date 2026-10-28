"""ECB mode (Electronic Codebook) for 16-bit blocks."""

from __future__ import annotations

from .feistel16 import (
    BLOCK_BYTES,
    CipherValueError,
    block_to_bytes,
    bytes_to_block,
    encrypt_block,
    decrypt_block,
)
from .padding import pad_pkcs7, unpad_pkcs7
from .results import BlockTrace


def encrypt_ecb(
    plaintext: bytes, key: int, collect_trace: bool = True
) -> tuple[bytes, list[BlockTrace]]:
    """Encrypt ``plaintext`` with ECB after PKCS#7 padding."""
    padded = pad_pkcs7(plaintext, BLOCK_BYTES)
    output = bytearray()
    blocks: list[BlockTrace] = []

    for offset in range(0, len(padded), BLOCK_BYTES):
        index = offset // BLOCK_BYTES
        plain_block = padded[offset : offset + BLOCK_BYTES]
        if collect_trace:
            cipher_int, rounds = encrypt_block(
                bytes_to_block(plain_block), key, collect_trace=collect_trace
            )
            cipher_block = block_to_bytes(cipher_int)
            blocks.append(
                BlockTrace(
                    index=index,
                    plaintext_block=plain_block,
                    ciphertext_block=cipher_block,
                    feistel_input=plain_block,
                    feistel_output=cipher_block,
                    feistel_rounds=rounds,
                )
            )
        else:
            cipher_int = encrypt_block(
                bytes_to_block(plain_block), key, collect_trace=collect_trace
            )
            cipher_block = block_to_bytes(cipher_int)
            blocks.append(
                BlockTrace(
                    index=index,
                    plaintext_block=plain_block,
                    ciphertext_block=cipher_block,
                    feistel_input=plain_block,
                    feistel_output=cipher_block,
                    feistel_rounds=[],
                )
            )
        output.extend(cipher_block)

    return bytes(output), blocks


def decrypt_ecb(ciphertext: bytes, key: int, collect_trace: bool = False) -> bytes:
    """Decrypt ECB ciphertext and validate/remove PKCS#7 padding."""
    if len(ciphertext) % BLOCK_BYTES != 0:
        raise CipherValueError(
            f"Panjang ciphertext ECB ({len(ciphertext)} byte) bukan kelipatan {BLOCK_BYTES} byte."
        )
    padded = bytearray()
    for offset in range(0, len(ciphertext), BLOCK_BYTES):
        cipher_block = ciphertext[offset : offset + BLOCK_BYTES]
        plain_int = decrypt_block(bytes_to_block(cipher_block), key, collect_trace=collect_trace)
        padded.extend(block_to_bytes(plain_int))
    return unpad_pkcs7(bytes(padded), BLOCK_BYTES)
