"""Test builder PDF laporan.

Inti pengujian: nilai di PDF harus cocok dengan objek hasil eksekusi aktual
(ModeResult), mode yang belum dijalankan ditandai "Belum dijalankan", status
verifikasi GAGAL tidak pernah ditulis sebagai keberhasilan, metadata kelompok
dan nama file tampil sesuai input pengguna.
"""

import re
import sys
from datetime import datetime, timezone
from io import BytesIO

import pytest
from pypdf import PdfReader

from crypto.pipeline import execute_mode, redecrypt_result
from reports import (
    Member,
    ReportMetadata,
    build_pdf_bytes,
    default_filename,
    resolve_filename,
    sanitize_filename,
)
from reports.pdf_report import ReportLabMissingError, build_findings

KEY = 0x1A2B
IV = 0x0F0F
COUNTER = 0x00C8
PLAINTEXT = "Halo dunia! Uji laporan PDF."


@pytest.fixture(scope="module")
def ecb_result():
    return execute_mode("ECB", PLAINTEXT, KEY)


@pytest.fixture(scope="module")
def cbc_result():
    return execute_mode("CBC", PLAINTEXT, KEY, iv=IV)


@pytest.fixture(scope="module")
def ctr_result():
    return execute_mode("CTR", PLAINTEXT, KEY, initial_counter=COUNTER)


@pytest.fixture()
def metadata():
    return ReportMetadata(
        title="Laporan Praktikum Kriptografi",
        group_name="Kelompok 3",
        course="Kriptografi Dasar",
        lecturer="Bapak Uji",
        class_name="IF-2A",
        members=[Member("Andi Wijaya", "2201234"), Member("Siti Rahma")],
        report_date="28 Oktober 2026",
        notes="Catatan uji.\nBaris kedua.",
        filename="",
    )


def _norm(pdf_bytes: bytes) -> tuple[str, int]:
    """Ekstrak teks PDF dan buang semua whitespace agar assert stabil."""
    reader = PdfReader(BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    return re.sub(r"\s+", "", text), len(reader.pages)


def test_pdf_contains_actual_ecb_data(metadata, ecb_result):
    pdf = build_pdf_bytes(metadata, {"ECB": ecb_result})
    norm, pages = _norm(pdf)
    assert pdf.startswith(b"%PDF")
    assert pages >= 2
    # setiap blok ciphertext/plaintext aktual tampil
    for block in ecb_result.blocks:
        assert block.ciphertext_block.hex().upper() in norm
        assert block.plaintext_block.hex().upper() in norm
    assert f"0x{KEY:04X}" in norm
    assert "BERHASIL" in norm
    # mode lain ditandai belum dijalankan
    assert norm.count("Belumdijalankan") >= 2
    # identitas kelompok dari input pengguna
    assert "Kelompok3" in norm and "LaporanPraktikumKriptografi" in norm
    assert "AndiWijaya" in norm and "2201234" in norm and "SitiRahma" in norm
    assert "KriptografiDasar" in norm and "BapakUji" in norm and "IF-2A" in norm
    assert "28Oktober2026" in norm


def test_pdf_all_modes(metadata, ecb_result, cbc_result, ctr_result):
    results = [ecb_result, cbc_result, ctr_result]
    pdf = build_pdf_bytes(metadata, results)
    norm, _ = _norm(pdf)

    for result in results:
        for block in result.blocks:
            assert block.ciphertext_block.hex().upper() in norm
            assert block.plaintext_block.hex().upper() in norm
    assert f"0x{IV:04X}" in norm          # IV CBC
    assert f"0x{COUNTER:04X}" in norm     # counter awal CTR
    assert "Belumdijalankan" not in norm  # tidak ada mode yang tersisa
    assert "GAGAL" not in norm            # semua verifikasi BERHASIL
    # lampiran memuat trace semua blok ECB
    assert f"ECB-Blok{ecb_result.block_count}" in norm


def test_pdf_empty_session_marks_all_modes(metadata):
    pdf = build_pdf_bytes(metadata, None)
    norm, pages = _norm(pdf)
    assert pages >= 2
    assert norm.count("Belumdijalankan") >= 3
    # tidak boleh ada status palsu
    assert "GAGAL" not in norm
    # ketiga bagian mode tetap ada dengan callout penjelas
    for mode in ("ECB", "CBC", "CTR"):
        assert f"Mode{mode}" in norm
        assert f"Belumdijalankan.Mode{mode}" in norm


def test_pdf_failed_verification_is_reported_as_gagal(metadata, ecb_result):
    wrong = redecrypt_result(ecb_result, key=0x00FF)
    assert wrong.verified is False

    pdf = build_pdf_bytes(metadata, {"ECB": wrong})
    norm, _ = _norm(pdf)
    assert "GAGAL" in norm
    assert "Round-tripECBGAGAL" in norm
    assert "berhasilantidapatdiberikan" in norm
    # frasa keberhasilan tidak boleh muncul untuk mode gagal
    assert "identikbyte-per-byte" not in norm


def test_pdf_accepts_single_result(metadata, ecb_result):
    pdf = build_pdf_bytes(metadata, ecb_result)
    norm, _ = _norm(pdf)
    assert ecb_result.blocks[0].ciphertext_block.hex().upper() in norm


def test_pdf_generated_timestamp(metadata, ecb_result):
    stamp = datetime(2026, 10, 28, 14, 0, 0, tzinfo=timezone.utc)
    pdf = build_pdf_bytes(metadata, {"ECB": ecb_result}, generated_at=stamp)
    norm, _ = _norm(pdf)
    assert "Dibuat28/10/202614:00:00UTC" in norm


def test_pdf_unicode_and_special_characters(metadata):
    md = ReportMetadata(
        title="Laporan — Praktikum <Kripto> & Uji",
        group_name="Kelompok Zoë",
        members=[Member("Zoë Müller", "22099")],
        notes="Baris satu\nBaris <dua> & tiga",
    )
    pdf = build_pdf_bytes(md, None)  # tidak boleh exception
    norm, _ = _norm(pdf)
    assert "Zoë" in norm and "Müller" in norm


def test_pdf_long_plaintext_tables_continue_across_pages(metadata):
    plaintext = ("Blok berulang ABCD. " * 20).strip()  # ~190 karakter -> ~96 blok ECB
    result = execute_mode("ECB", plaintext, KEY)
    pdf = build_pdf_bytes(metadata, {"ECB": result})
    norm, pages = _norm(pdf)
    assert pages >= 5  # tabel menerus ke beberapa halaman
    last = result.blocks[-1]
    assert last.ciphertext_block.hex().upper() in norm  # blok terakhir tidak terpotong
    assert f"ECB-Blok{result.block_count}" in norm       # lampiran trace blok terakhir


def test_pdf_empty_plaintext_modes(metadata):
    ecb = execute_mode("ECB", "", KEY)
    ctr = execute_mode("CTR", "", KEY, initial_counter=COUNTER)
    pdf = build_pdf_bytes(metadata, [ecb, ctr])
    norm, _ = _norm(pdf)
    assert "Belumdijalankan" in norm                      # CBC belum dijalankan
    # ECB kosong tetap punya 1 blok padding; CTR kosong tidak punya blok
    assert ecb.blocks[0].ciphertext_block.hex().upper() in norm
    assert "Plaintextkosong" in norm


def test_build_findings_no_results():
    findings = build_findings({})
    assert findings and "belum ada mode" in findings[0].lower()


def test_build_findings_all_verified(ecb_result, cbc_result, ctr_result):
    findings = build_findings({"ECB": ecb_result, "CBC": cbc_result, "CTR": ctr_result})
    joined = " ".join(findings)
    assert "3 mode dijalankan dan 3" in joined
    assert "Round-trip ECB BERHASIL" in joined
    assert "belum dijalankan" not in joined.lower()


# ---------------------------------------------------------------------------
# Nama file
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw,expected", [
    ("Kelompok 3", "Kelompok_3"),
    ('a<b>:"/\\|?*c', "a_c"),
    ("  spasi  ganda  ", "spasi_ganda"),
    ("..", "Laporan_CipherLab"),
    ("", "Laporan_CipherLab"),
    ("___", "Laporan_CipherLab"),
    ("CON", "Laporan_CON"),
    ("report.pdf", "report.pdf"),
    ("Zoë ñ", "Zoë_ñ"),
    ("Kelompok 3: Laporan *Final* v2?", "Kelompok_3_Laporan_Final_v2"),
])
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitize_filename_length_limit():
    assert len(sanitize_filename("A" * 300)) <= 80


def test_default_filename_prefers_group(metadata):
    assert default_filename("Kelompok 3", "Judul Apa Pun") == "Laporan_CipherLab_Kelompok_3"
    assert default_filename("", "Judul Menarik") == "Laporan_CipherLab_Judul_Menarik"
    assert default_filename("", "") == "Laporan_CipherLab"


def test_resolve_filename_user_choice_then_sanitized():
    md = ReportMetadata(title="T", group_name="G", filename="Nama Keren: v2?")
    assert resolve_filename(md) == "Nama_Keren_v2"
    md2 = ReportMetadata(title="Judul", group_name="Kelompok 5", filename="   ")
    assert resolve_filename(md2) == "Laporan_CipherLab_Kelompok_5"


# ---------------------------------------------------------------------------
# Validasi metadata & dependensi
# ---------------------------------------------------------------------------


def test_metadata_validation():
    with pytest.raises(ValueError, match="Judul"):
        ReportMetadata(title="", group_name="G").validate()
    with pytest.raises(ValueError, match="kelompok"):
        ReportMetadata(title="T", group_name="  ").validate()
    with pytest.raises(ValueError, match="NIM tanpa nama"):
        ReportMetadata(title="T", group_name="G", members=[Member("", "123")]).validate()
    # baris anggota kosong sah (diabaikan builder)
    ReportMetadata(title="T", group_name="G", members=[Member("", "")]).validate()


def test_build_rejects_invalid_metadata():
    with pytest.raises(ValueError):
        build_pdf_bytes(ReportMetadata(title="", group_name=""), None)


def test_reportlab_missing_error_message(monkeypatch, metadata):
    monkeypatch.setitem(sys.modules, "reportlab.lib", None)
    with pytest.raises(ReportLabMissingError, match="pip install reportlab"):
        build_pdf_bytes(metadata, None)
