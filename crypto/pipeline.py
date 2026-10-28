"""High-level execution pipeline used by the Streamlit UI and tests."""

from __future__ import annotations

from datetime import datetime

from .cbc import decrypt_cbc, encrypt_cbc
from .ctr import decrypt_ctr, encrypt_ctr
from .ecb import decrypt_ecb, encrypt_ecb
from .encoding import bytes_to_text, text_to_bytes
from .feistel16 import BLOCK_BITS, BLOCK_BYTES, CipherValueError, MAX_KEY
from .results import ModeResult

SUPPORTED_MODES = ("ECB", "CBC", "CTR")


def normalize_mode(mode: str) -> str:
    normalized = str(mode).strip().upper()
    if normalized not in SUPPORTED_MODES:
        raise ValueError(f"Mode tidak dikenal: {mode!r}. Gunakan ECB, CBC, atau CTR.")
    return normalized


def _encrypt(mode: str, plaintext: bytes, key: int, iv, counter, collect_trace: bool):
    if mode == "ECB":
        return encrypt_ecb(plaintext, key, collect_trace=collect_trace)
    if mode == "CBC":
        if iv is None:
            raise CipherValueError("Mode CBC membutuhkan IV 16-bit.")
        return encrypt_cbc(plaintext, key, iv, collect_trace=collect_trace)
    if counter is None:
        raise CipherValueError("Mode CTR membutuhkan initial counter 16-bit.")
    return encrypt_ctr(plaintext, key, counter, collect_trace=collect_trace)


def _decrypt(mode: str, ciphertext: bytes, key: int, iv, counter) -> bytes:
    if mode == "ECB":
        return decrypt_ecb(ciphertext, key)
    if mode == "CBC":
        if iv is None:
            raise CipherValueError("Mode CBC membutuhkan IV 16-bit.")
        return decrypt_cbc(ciphertext, key, iv)
    if counter is None:
        raise CipherValueError("Mode CTR membutuhkan initial counter 16-bit.")
    return decrypt_ctr(ciphertext, key, counter)


def execute_mode(
    mode: str,
    plaintext_text: str,
    key: int,
    iv: int | None = None,
    initial_counter: int | None = None,
    collect_trace: bool = True,
) -> ModeResult:
    """Run encryption and verification decryption for one mode.

    All stored values come from the actual computation. Errors are raised so
    the caller can show a validation message; no partial/fake result is stored.
    """
    normalized = normalize_mode(mode)
    if not isinstance(key, int) or not 0 <= key <= MAX_KEY:
        raise CipherValueError("Kunci harus berupa bilangan bulat 16-bit.")

    plaintext = text_to_bytes(plaintext_text)
    ciphertext, blocks = _encrypt(
        normalized, plaintext, key, iv, initial_counter, collect_trace
    )

    decrypted_bytes = b""
    decrypted_text = ""
    error = None
    try:
        decrypted_bytes = _decrypt(normalized, ciphertext, key, iv, initial_counter)
        decrypted_text = bytes_to_text(decrypted_bytes)
    except (CipherValueError, ValueError) as exc:
        error = str(exc)

    verified = decrypted_bytes == plaintext and error is None

    return ModeResult(
        mode=normalized,
        plaintext_text=plaintext_text,
        plaintext_bytes=plaintext,
        key=key,
        iv=iv if normalized == "CBC" else None,
        initial_counter=initial_counter if normalized == "CTR" else None,
        ciphertext=ciphertext,
        blocks=blocks,
        decrypted_bytes=decrypted_bytes,
        decrypted_text=decrypted_text,
        verified=verified,
        executed_at=datetime.now().astimezone(),
        encoding="UTF-8",
        padding=None if normalized == "CTR" else f"PKCS#7 ({BLOCK_BYTES} byte)",
        decryption_error=error,
    )


def redecrypt_result(
    result: ModeResult,
    key: int | None = None,
    iv: int | None = None,
    initial_counter: int | None = None,
) -> ModeResult:
    """Run decryption again against the stored ciphertext and update status.

    This is used by the Playground "Decrypt" button. A wrong key/IV/counter can
    legitimately make verification fail; that failure is recorded exactly as
    it happened, never replaced with a success.
    """
    use_key = result.key if key is None else key
    use_iv = result.iv if iv is None else iv
    use_counter = result.initial_counter if initial_counter is None else initial_counter

    try:
        decrypted = _decrypt(result.mode, result.ciphertext, use_key, use_iv, use_counter)
        result.decrypted_bytes = decrypted
        result.decrypted_text = bytes_to_text(decrypted)
        result.decryption_error = None
        result.verified = decrypted == result.plaintext_bytes
    except (CipherValueError, ValueError) as exc:
        result.decrypted_bytes = b""
        result.decrypted_text = ""
        result.decryption_error = str(exc)
        result.verified = False
    return result


__all__ = [
    "SUPPORTED_MODES",
    "normalize_mode",
    "execute_mode",
    "redecrypt_result",
    "BLOCK_BITS",
]
