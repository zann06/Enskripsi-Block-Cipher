"""Test pipeline eksekusi tingkat tinggi dan struktur ModeResult."""

import pytest

from crypto.feistel16 import CipherValueError
from crypto.pipeline import execute_mode, normalize_mode, redecrypt_result
from crypto.results import BlockTrace, ModeResult


def test_normalize_mode():
    assert normalize_mode("ecb") == "ECB"
    assert normalize_mode(" CTR ") == "CTR"
    with pytest.raises(ValueError):
        normalize_mode("GCM")


@pytest.mark.parametrize("mode,kwargs", [
    ("ECB", {}),
    ("CBC", {"iv": 0x0F0F}),
    ("CTR", {"initial_counter": 0x00C8}),
])
def test_execute_mode_produces_verified_result(mode, kwargs):
    plaintext = "Halo dunia! Uji tiga mode."
    result = execute_mode(mode, plaintext, 0x1A2B, **kwargs)
    assert isinstance(result, ModeResult)
    assert result.mode == mode
    assert result.verified is True
    assert result.status == "BERHASIL"
    assert result.decrypted_text == plaintext
    assert result.decrypted_bytes == result.plaintext_bytes
    assert result.encoding == "UTF-8"
    assert result.block_count == len(result.blocks)
    assert result.ciphertext_length == len(result.ciphertext)
    assert result.mode_label.startswith(mode)
    if mode == "ECB":
        assert result.iv is None and result.initial_counter is None
        assert result.padding == "PKCS#7 (2 byte)"
    if mode == "CBC":
        assert result.iv == 0x0F0F and result.initial_counter is None
    if mode == "CTR":
        assert result.initial_counter == 0x00C8 and result.iv is None
        assert result.padding is None


def test_execute_mode_blocks_match_plaintext_length():
    plaintext = "Halo dunia! Uji tiga mode."  # 26 byte
    for mode, kwargs in (("ECB", {}), ("CBC", {"iv": 1}), ("CTR", {"initial_counter": 0})):
        result = execute_mode(mode, plaintext, 0x1A2B, **kwargs)
        if mode == "CTR":
            assert result.block_count == 13
        else:
            assert result.block_count == 14  # PKCS#7 menambah 1 blok penuh


def test_execute_mode_rejects_bad_inputs():
    with pytest.raises(CipherValueError):
        execute_mode("ECB", "data", 0x10000)
    with pytest.raises(CipherValueError):
        execute_mode("CBC", "data", 0x1A2B, iv=None)
    with pytest.raises(CipherValueError):
        execute_mode("CTR", "data", 0x1A2B, initial_counter=None)


def test_redecrypt_wrong_key_records_failure_honestly():
    """Kunci salah harus menghasilkan status GAGAL, bukan sukses palsu."""
    result = execute_mode("CBC", "Halo dunia!", 0x1A2B, iv=0x0F0F)
    assert result.verified is True

    wrong = redecrypt_result(result, key=0x0F0E)
    assert wrong.verified is False
    assert wrong.status == "GAGAL"
    assert wrong.decryption_error  # padding/UTF-8 tidak valid

    restored = redecrypt_result(result, key=0x1A2B)
    assert restored.verified is True
    assert restored.decryption_error is None


def test_redecrypt_ctr_wrong_counter_fails():
    result = execute_mode("CTR", "Halo dunia!", 0x1A2B, initial_counter=0x00C8)
    wrong = redecrypt_result(result, initial_counter=0x00C9)
    assert wrong.verified is False


def test_redecrypt_wrong_key_creates_independent_result():
    """ModeResult asli tidak boleh ikut berubah ketika redecrypt gagal."""
    result = execute_mode("ECB", "Halo dunia!", 0x1A2B)
    original_ciphertext = result.ciphertext
    original_blocks = list(result.blocks)
    redecrypt_result(result, key=0x00FF)
    assert result.ciphertext == original_ciphertext
    assert result.blocks == original_blocks


def test_blocktrace_properties():
    block = BlockTrace(
        index=0,
        plaintext_block=b"\x01\x02",
        ciphertext_block=b"\x03\x04",
        feistel_input=b"\x01\x02",
        feistel_output=b"\x03\x04",
        counter_block=b"\x00\xc8",
    )
    assert block.number == 1
    assert block.keystream == b"\x03\x04"
    no_counter = BlockTrace(
        index=2,
        plaintext_block=b"\x01\x02",
        ciphertext_block=b"\x03\x04",
        feistel_input=b"\x01\x02",
        feistel_output=b"\x03\x04",
    )
    assert no_counter.number == 3
    assert no_counter.keystream is None


def test_executed_at_is_aware_datetime():
    result = execute_mode("ECB", "x", 0x1A2B)
    assert result.executed_at.tzinfo is not None
