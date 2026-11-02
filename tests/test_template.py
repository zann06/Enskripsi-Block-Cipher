"""Test profil template laporan (tampilan & susunan bagian).

Fokus: template hanya mengubah presentasi/struktur, tidak mengubah data
eksekusi; bagian yang dinonaktifkan hilang; urutan judul mengikuti template;
serialisasi JSON/YAML bolak-balik konsisten; input tak valid tidak merusak
laporan.
"""

import base64
import re
from io import BytesIO

import pytest
from pypdf import PdfReader

from crypto.pipeline import execute_mode
from reports import (
    DEFAULT_SECTIONS,
    Member,
    ReportMetadata,
    ReportTemplate,
    build_pdf_bytes,
    load_template_text,
    template_from_dict,
    template_from_json,
    template_from_yaml,
    template_to_dict,
    template_to_json,
)
from reports.pdf_report import _logo_flowable

KEY = 0x1A2B
PLAINTEXT = "Halo dunia! Uji template laporan."

# PNG 1x1 transparan (valid).
_PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


@pytest.fixture(scope="module")
def ecb_result():
    return execute_mode("ECB", PLAINTEXT, KEY)


@pytest.fixture()
def metadata():
    return ReportMetadata(
        title="Laporan Praktikum Kriptografi",
        group_name="Kelompok 3",
        members=[Member("Andi Wijaya", "2201234")],
        report_date="28 Oktober 2026",
    )


def _norm(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    norm = re.sub(r"\s+", "", text)
    norm = re.sub(r"Dibuat\d{2}/\d{2}/\d{4}\d{2}:\d{2}:\d{2}", "", norm)
    norm = re.sub(r"Halaman\d+", "", norm)
    return norm


# ---------------------------------------------------------------------------
# Normalisasi & serialisasi
# ---------------------------------------------------------------------------


def test_default_template_sections():
    assert ReportTemplate().normalized().sections == DEFAULT_SECTIONS


@pytest.mark.parametrize("raw,expected", [
    ("#abc", "#AABBCC"),
    ("1a2b3c", "#1A2B3C"),
    ("#123456", "#123456"),
    ("bukan warna", "#1A1A1A"),
    ("", "#1A1A1A"),
])
def test_accent_color_normalization(raw, expected):
    assert ReportTemplate(accent_color=raw).normalized().accent_color == expected


def test_font_family_fallback():
    assert ReportTemplate(font_family="comic").normalized().font_family == "vera"
    assert ReportTemplate(font_family="Times").normalized().font_family == "times"


def test_sections_filtered_and_deduplicated():
    tpl = ReportTemplate(sections=("summary", "bogus", "summary", "ecb")).normalized()
    assert tpl.sections == ("summary", "ecb")


def test_sections_accept_comma_string():
    tpl = ReportTemplate(sections="summary, ecb, ctr").normalized()  # type: ignore[arg-type]
    assert tpl.sections == ("summary", "ecb", "ctr")


def test_explicit_empty_sections_kept():
    assert ReportTemplate(sections=()).normalized().sections == ()


def test_heading_for_uses_number_and_override():
    tpl = ReportTemplate(section_titles={"summary": "Ikhtisar"}).normalized()
    assert tpl.heading_for("summary", 1) == "1. Ikhtisar"
    assert tpl.heading_for("toc") == "Daftar Isi"


def test_json_roundtrip_without_logo():
    tpl = ReportTemplate(institution="Universitas Contoh", accent_color="#0A5", font_family="times")
    data = template_to_dict(tpl)
    assert "logo_base64" not in data
    again = template_from_json(template_to_json(tpl))
    assert again.institution == "Universitas Contoh"
    assert again.accent_color == "#00AA55"
    assert again.font_family == "times"


def test_json_roundtrip_with_logo():
    tpl = ReportTemplate(logo=_PNG_1PX).normalized()
    again = template_from_dict(template_to_dict(tpl))
    assert again.logo == _PNG_1PX


def test_template_from_dict_rejects_non_mapping():
    with pytest.raises(ValueError):
        template_from_dict(["bukan", "objek"])


def test_template_from_json_invalid():
    with pytest.raises(ValueError, match="JSON"):
        template_from_json("{bukan json}")


def test_yaml_load():
    tpl = template_from_yaml(
        "institution: Universitas YAML\n"
        "accent_color: '#FF8800'\n"
        "sections:\n"
        "  - summary\n"
        "  - ecb\n"
    )
    assert tpl.institution == "Universitas YAML"
    assert tpl.accent_color == "#FF8800"
    assert tpl.sections == ("summary", "ecb")


def test_load_template_text_autodetect():
    assert load_template_text('{"institution": "JSON"}', "x.txt").institution == "JSON"
    assert load_template_text("institution: YAML\n", "x.yaml").institution == "YAML"


def test_load_template_text_invalid_yaml():
    with pytest.raises(ValueError, match="YAML"):
        load_template_text("a: [1,\n", "x.yaml")


# ---------------------------------------------------------------------------
# Dampak pada PDF
# ---------------------------------------------------------------------------


def test_pdf_default_matches_baseline(metadata, ecb_result):
    norm = _norm(build_pdf_bytes(metadata, {"ECB": ecb_result}))
    assert "1.RingkasanEksekusi" in norm
    assert "9.BatasandanPeringatanKeamanan" in norm


def test_pdf_custom_section_title_and_omitted_section(metadata, ecb_result):
    tpl = ReportTemplate(
        sections=("summary", "ecb"),
        section_titles={"summary": "Ikhtisar Eksekusi"},
    )
    norm = _norm(build_pdf_bytes(metadata, {"ECB": ecb_result}, template=tpl))
    assert "1.IkhtisarEksekusi" in norm
    assert "BatasandanPeringatanKeamanan" not in norm
    assert "TujuandanRuangLingkup" not in norm


def test_pdf_section_reordering(metadata, ecb_result):
    tpl = ReportTemplate(sections=("limitations", "summary"))
    norm = _norm(build_pdf_bytes(metadata, {"ECB": ecb_result}, template=tpl))
    assert "1.BatasandanPeringatanKeamanan" in norm
    assert "2.RingkasanEksekusi" in norm
    assert norm.index("BatasandanPeringatanKeamanan") < norm.index("RingkasanEksekusi")


def test_pdf_custom_header_footer_institution(metadata, ecb_result):
    tpl = ReportTemplate(
        institution="Universitas Contoh",
        header_text="Kripto - Kelompok 3",
        footer_text="Dokumen internal laboratorium.",
    )
    norm = _norm(build_pdf_bytes(metadata, {"ECB": ecb_result}, template=tpl))
    assert "UniversitasContoh" in norm
    assert "Kripto-Kelompok3" in norm
    assert "Dokumeninternallaboratorium." in norm


def test_pdf_font_families_build(metadata, ecb_result):
    for family in ("vera", "helvetica", "times"):
        pdf = build_pdf_bytes(metadata, {"ECB": ecb_result}, template=ReportTemplate(font_family=family))
        assert pdf.startswith(b"%PDF")


def test_pdf_with_logo_does_not_crash(metadata, ecb_result):
    pdf = build_pdf_bytes(metadata, {"ECB": ecb_result}, template=ReportTemplate(logo=_PNG_1PX))
    assert pdf.startswith(b"%PDF")


def test_logo_flowable_handles_garbage():
    assert _logo_flowable(None) is None
    assert _logo_flowable(b"bukan gambar") is None
    assert _logo_flowable(_PNG_1PX) is not None


def test_template_does_not_alter_verification_status(metadata, ecb_result):
    """Template tidak boleh menyembunyikan status GAGAL/berhasil."""
    norm = _norm(build_pdf_bytes(metadata, {"ECB": ecb_result}, template=ReportTemplate()))
    assert "BERHASIL" in norm
