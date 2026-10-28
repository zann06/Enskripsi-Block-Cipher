"""CipherLab cryptographic building blocks.

This package implements a *toy* 16-bit Feistel network and the ECB, CBC, and
CTR modes for educational use only. It must never be used to protect real data.
"""

from .feistel16 import (
    BLOCK_BITS,
    BLOCK_BYTES,
    ROUNDS,
    decrypt_block,
    encrypt_block,
    key_schedule,
)
from .padding import PaddingError, pad_pkcs7, unpad_pkcs7

__all__ = [
    "BLOCK_BITS",
    "BLOCK_BYTES",
    "ROUNDS",
    "encrypt_block",
    "decrypt_block",
    "key_schedule",
    "pad_pkcs7",
    "unpad_pkcs7",
    "PaddingError",
]
