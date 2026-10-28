"""CBC mode (Cipher Block Chaining) for 16-bit blocks."""

from __future__ import annotations

from .feistel16 import (
    BLOCK_BYTES,
    CipherValueError,
    block_to_bytes,
    bytes_to_block,
    decrypt_block,
    encrypt_block,
    validate_int16,
    xor_blocks,
)
from .padding import pad_pkcs7, unpad_pkcs7
from .results import BlockTrace


def encrypt_cbc(
    plaintext: bytes, key: int, iv: int, collect_trace: bool = True
) -> tuple[bytes, list[BlockTrace]]:
    """Encrypt with CBC: ``C_i = E_K(P_i XOR C_(i-1))``, ``C_0 = IV``."""
    validate_int16(iv, "IV")
    padded = pad_pkcs7(plaintext, BLOCK_BYTES)
    previous = block_to_bytes(iv)
    output = bytearray()
    blocks: list[BlockTrace] = []

    for offset in range(0, len(padded), BLOCK_BYTES):
        index = offset // BLOCK_BYTES
        plain_block = padded[offset : offset + BLOCK_BYTES]
        xored = xor_blocks(plain_block, previous)
        cipher_int, rounds = encrypt_block(
            bytes_to_block(xored), key, collect_trace=collect_trace
        )
        cipher_block = block_to_bytes(cipher_int)
        output.extend(cipher_block)
        blocks.append(
            BlockTrace(
                index=index,
                plaintext_block=plain_block,
                ciphertext_block=cipher_block,
                feistel_input=xored,
                feistel_output=cipher_block,
                xor_value=previous,
                xor_result=xored,
                feistel_rounds=rounds if collect_trace else [],
            )
        )
        previous = cipher_block

    return bytes(output), blocks


def decrypt_cbc(
    ciphertext: bytes, key: int, iv: int, collect_trace: bool = False
) -> bytes:
    """Decrypt CBC: ``P_i = D_K(C_i) XOR C_(i-1)``; validate PKCS#7 padding."""
    validate_int16(iv, "IV")
    if len(ciphertext) % BLOCK_BYTES != 0:
        raise CipherValueError(
            f"Panjang ciphertext CBC ({len(ciphertext)} byte) bukan kelipatan {BLOCK_BYTES} byte."
        )
    previous = block_to_bytes(iv)
    padded = bytearray()

    for offset in range(0, len(ciphertext), BLOCK_BYTES):
        cipher_block = ciphertext[offset : offset + BLOCK_BYTES]
        plain_int = decrypt_block(bytes_to_block(cipher_block), key, collect_trace=collect_trace)
        padded.extend(xor_blocks(block_to_bytes(plain_int), previous))
        previous = cipher_block

    return unpad_pkcs7(bytes(padded), BLOCK_BYTES)
