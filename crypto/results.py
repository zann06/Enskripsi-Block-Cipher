"""Typed execution results shared by the UI, tests, and PDF report builder.

Every value in these objects comes from a real call to the cipher/mode
functions. The report builder never generates ciphertext or traces itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .feistel16 import RoundTrace


@dataclass
class BlockTrace:
    """Actual per-block computation data for one mode execution.

    ``xor_value``/``xor_result`` are mode specific:

    * ECB: no XOR (``None``).
    * CBC: ``xor_value`` is IV or previous ciphertext, ``xor_result`` is the
      block fed into the Feistel cipher.
    * CTR: ``xor_value`` is the keystream, ``xor_result`` equals the resulting
      ciphertext block (plaintext XOR keystream).
    """

    index: int
    plaintext_block: bytes
    ciphertext_block: bytes
    feistel_input: bytes
    feistel_output: bytes
    xor_value: bytes | None = None
    xor_result: bytes | None = None
    counter_block: bytes | None = None
    feistel_rounds: list[RoundTrace] = field(default_factory=list)

    @property
    def number(self) -> int:
        """1-based block number for display."""
        return self.index + 1

    @property
    def keystream(self) -> bytes | None:
        """CTR keystream (the Feistel output)."""
        return self.feistel_output if self.counter_block is not None else None


@dataclass
class ModeResult:
    """One complete mode execution: encryption plus decryption verification."""

    mode: str
    plaintext_text: str
    plaintext_bytes: bytes
    key: int
    ciphertext: bytes
    blocks: list[BlockTrace]
    decrypted_bytes: bytes
    decrypted_text: str
    verified: bool
    executed_at: datetime
    iv: int | None = None
    initial_counter: int | None = None
    encoding: str = "UTF-8"
    padding: str | None = "PKCS#7 (2 byte)"
    decryption_error: str | None = None

    @property
    def status(self) -> str:
        return "BERHASIL" if self.verified else "GAGAL"

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    @property
    def ciphertext_length(self) -> int:
        return len(self.ciphertext)

    @property
    def mode_label(self) -> str:
        return {
            "ECB": "ECB (Electronic Codebook)",
            "CBC": "CBC (Cipher Block Chaining)",
            "CTR": "CTR (Counter)",
        }.get(self.mode.upper(), self.mode.upper())
