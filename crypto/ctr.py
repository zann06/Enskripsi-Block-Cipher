"""CTR mode (Counter) for 16-bit blocks."""

from __future__ import annotations

from .feistel16 import (
    BLOCK_BYTES,
    CipherValueError,
    block_to_bytes,
    bytes_to_block,
    encrypt_block,
    validate_int16,
)
from .results import BlockTrace

COUNTER_LIMIT = 0xFFFF


class CounterOverflowError(CipherValueError):
    """Raised when the 16-bit counter would wrap past 0xFFFF."""


def _keystream(initial_counter: int, block_count: int, key: int, collect_trace: bool):
    validate_int16(initial_counter, "Counter awal")
    if block_count == 0:
        return []
    last_counter = initial_counter + block_count - 1
    if last_counter > COUNTER_LIMIT:
        raise CounterOverflowError(
            "Counter 16-bit akan overflow: "
            f"counter awal 0x{initial_counter:04X} + {block_count} blok "
            f"melewati 0x{COUNTER_LIMIT:04X}. Pilih counter yang lebih kecil "
            "atau perpendek plaintext."
        )
    streams = []
    for index in range(block_count):
        counter = initial_counter + index
        if collect_trace:
            stream_int, rounds = encrypt_block(counter, key, collect_trace=True)
        else:
            stream_int = encrypt_block(counter, key, collect_trace=False)
            rounds = []
        streams.append((counter, block_to_bytes(stream_int), rounds))
    return streams


def _xor_partial(data: bytes, keystream: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, keystream[: len(data)]))


def encrypt_ctr(
    plaintext: bytes, key: int, initial_counter: int, collect_trace: bool = True
) -> tuple[bytes, list[BlockTrace]]:
    """Encrypt with CTR: ``C_i = P_i XOR E_K(T_i)``, ``T_i = counter + i``."""
    block_count = (len(plaintext) + BLOCK_BYTES - 1) // BLOCK_BYTES
    streams = _keystream(initial_counter, block_count, key, collect_trace)
    output = bytearray()
    blocks: list[BlockTrace] = []

    for index, (counter, stream, rounds) in enumerate(streams):
        offset = index * BLOCK_BYTES
        plain_block = plaintext[offset : offset + BLOCK_BYTES]
        cipher_block = _xor_partial(plain_block, stream)
        output.extend(cipher_block)
        blocks.append(
            BlockTrace(
                index=index,
                plaintext_block=plain_block,
                ciphertext_block=cipher_block,
                feistel_input=block_to_bytes(counter),
                feistel_output=stream,
                xor_value=stream,
                xor_result=cipher_block,
                counter_block=block_to_bytes(counter),
                feistel_rounds=rounds if collect_trace else [],
            )
        )

    return bytes(output), blocks


def decrypt_ctr(
    ciphertext: bytes, key: int, initial_counter: int, collect_trace: bool = False
) -> bytes:
    """Decrypt CTR by regenerating the same keystream (no padding)."""
    block_count = (len(ciphertext) + BLOCK_BYTES - 1) // BLOCK_BYTES
    streams = _keystream(initial_counter, block_count, key, collect_trace)
    output = bytearray()
    for index, (_counter, stream, _rounds) in enumerate(streams):
        offset = index * BLOCK_BYTES
        cipher_block = ciphertext[offset : offset + BLOCK_BYTES]
        output.extend(_xor_partial(cipher_block, stream))
    return bytes(output)
