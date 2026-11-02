"""Profil template laporan: kustomisasi tampilan dan struktur laporan PDF.

Profil ini **hanya** mengubah presentasi (warna aksen, font, logo institusi,
teks header/footer, judul bagian, serta bagian mana yang disertakan dan
urutannya). Isi laporan tetap sepenuhnya berasal dari data eksekusi aktual;
modul ini tidak pernah membuat atau mengubah ciphertext, trace, maupun status
verifikasi.

Profil dapat dibuat lewat UI aplikasi (Tingkat A) maupun dimuat dari berkas
JSON/YAML berisi kunci yang sama (Tingkat B), sehingga template bisa dibuat
dosen/asisten lalu dibagikan ke mahasiswa.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

__all__ = [
    "DEFAULT_ACCENT",
    "DEFAULT_HEADER_TEXT",
    "DEFAULT_FOOTER_TEXT",
    "DEFAULT_SECTIONS",
    "FONT_FAMILIES",
    "FONT_LABELS",
    "NUMBERED_SECTIONS",
    "SECTION_KEYS",
    "SECTION_LABELS",
    "ReportTemplate",
    "load_template_text",
    "template_from_dict",
    "template_from_json",
    "template_from_yaml",
    "template_to_dict",
    "template_to_json",
]

DEFAULT_ACCENT = "#1A1A1A"
DEFAULT_HEADER_TEXT = "CipherLab - Laporan Block Cipher 16-bit"
DEFAULT_FOOTER_TEXT = (
    "CipherLab - laporan dibuat lokal dengan ReportLab; "
    "toy cipher 16-bit, bukan untuk data nyata."
)

# Pilihan font yang aman tersedia di ReportLab tanpa berkas eksternal.
FONT_FAMILIES = ("vera", "helvetica", "times")
FONT_LABELS = {
    "vera": "Vera (bawaan, cakupan Latin luas)",
    "helvetica": "Helvetica",
    "times": "Times (serif)",
}

# Urutan default bagian laporan (kunci internal, urut).
SECTION_KEYS = (
    "toc",
    "summary",
    "purpose",
    "algorithm",
    "ecb",
    "cbc",
    "ctr",
    "comparison",
    "conclusion",
    "limitations",
    "appendix",
)
DEFAULT_SECTIONS = SECTION_KEYS

SECTION_LABELS = {
    "toc": "Daftar Isi",
    "summary": "Ringkasan Eksekusi",
    "purpose": "Tujuan dan Ruang Lingkup",
    "algorithm": "Algoritma dan Rumus Mode",
    "ecb": "Mode ECB",
    "cbc": "Mode CBC",
    "ctr": "Mode CTR",
    "comparison": "Perbandingan Mode",
    "conclusion": "Analisis dan Kesimpulan",
    "limitations": "Batasan dan Peringatan Keamanan",
    "appendix": "Lampiran (Trace Ronde & Jadwal Kunci)",
}

# Bagian yang diberi nomor urut pada judul (Lampiran & Daftar Isi tidak).
NUMBERED_SECTIONS = frozenset(
    {"summary", "purpose", "algorithm", "ecb", "cbc", "ctr", "comparison", "conclusion", "limitations"}
)

_ACCENT_RE = re.compile(r"^#?([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


def normalize_accent_color(value: object) -> str | None:
    """Normalisasi warna hex menjadi ``#RRGGBB`` (huruf besar) atau ``None``."""
    if value is None:
        return None
    match = _ACCENT_RE.match(str(value).strip())
    if not match:
        return None
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return "#" + digits.upper()


def _coerce_sections(values: object) -> tuple[str, ...]:
    """Saring daftar bagian: hanya kunci valid, tanpa duplikat, urut tetap."""
    if values is None:
        return DEFAULT_SECTIONS
    if isinstance(values, str):
        values = [part.strip() for part in values.split(",")]
    if not isinstance(values, (list, tuple, set)):
        return DEFAULT_SECTIONS
    raw = [str(item).strip().lower() for item in values]
    seen: list[str] = []
    for key in raw:
        if key in SECTION_KEYS and key not in seen:
            seen.append(key)
    if seen:
        return tuple(seen)
    # Daftar kosong eksplisit berarti "tanpa bagian"; daftar berisi
    # namun tak ada kunci valid diperlakukan sebagai salah ketik -> bawaan.
    return () if not raw else DEFAULT_SECTIONS


@dataclass
class ReportTemplate:
    """Profil tampilan laporan; semua bidang opsional."""

    institution: str = ""
    accent_color: str = DEFAULT_ACCENT
    font_family: str = "vera"
    header_text: str = ""
    footer_text: str = ""
    sections: tuple[str, ...] = DEFAULT_SECTIONS
    section_titles: dict[str, str] = field(default_factory=dict)
    logo: bytes | None = None

    def normalized(self) -> "ReportTemplate":
        """Kembalikan salinan bersih: warna/font/urutan bagian tervalidasi."""
        accent = normalize_accent_color(self.accent_color) or DEFAULT_ACCENT
        font = str(self.font_family or "vera").strip().lower()
        if font not in FONT_FAMILIES:
            font = "vera"
        titles = {
            str(key).strip().lower(): str(value).strip()
            for key, value in (self.section_titles or {}).items()
            if str(key).strip().lower() in SECTION_KEYS and str(value).strip()
        }
        return ReportTemplate(
            institution=str(self.institution or "").strip(),
            accent_color=accent,
            font_family=font,
            header_text=str(self.header_text or "").strip(),
            footer_text=str(self.footer_text or "").strip(),
            sections=_coerce_sections(self.sections),
            section_titles=titles,
            logo=self.logo or None,
        )

    def heading_for(self, key: str, number: int | None = None) -> str:
        """Judul bagian final: override pengguna atau label bawaan, plus nomor."""
        base = self.section_titles.get(key) or SECTION_LABELS.get(key, key)
        if number is not None and key in NUMBERED_SECTIONS:
            return f"{number}. {base}"
        return base


# ---------------------------------------------------------------------------
# Serialisasi JSON / YAML
# ---------------------------------------------------------------------------


def template_to_dict(template: ReportTemplate) -> dict[str, Any]:
    """Ubah profil menjadi dict JSON-serializable (logo sebagai base64)."""
    clean = template.normalized()
    data: dict[str, Any] = {
        "institution": clean.institution,
        "accent_color": clean.accent_color,
        "font_family": clean.font_family,
        "header_text": clean.header_text,
        "footer_text": clean.footer_text,
        "sections": list(clean.sections),
        "section_titles": dict(clean.section_titles),
    }
    if clean.logo:
        data["logo_base64"] = base64.b64encode(clean.logo).decode("ascii")
    return data


def template_from_dict(data: object) -> ReportTemplate:
    """Bangun profil dari dict; bidang tak dikenal diabaikan."""
    if not isinstance(data, Mapping):
        raise ValueError("Template harus berupa objek (dict) berisi pengaturan.")
    logo: bytes | None = None
    encoded = data.get("logo_base64")
    if encoded:
        try:
            logo = base64.b64decode(str(encoded), validate=True)
        except (binascii.Error, ValueError):
            logo = None
    titles = data.get("section_titles")
    if not isinstance(titles, Mapping):
        titles = {}
    return ReportTemplate(
        institution=str(data.get("institution", "") or ""),
        accent_color=str(data.get("accent_color", DEFAULT_ACCENT) or DEFAULT_ACCENT),
        font_family=str(data.get("font_family", "vera") or "vera"),
        header_text=str(data.get("header_text", "") or ""),
        footer_text=str(data.get("footer_text", "") or ""),
        sections=_coerce_sections(data.get("sections")),
        section_titles=dict(titles),
        logo=logo,
    ).normalized()


def template_to_json(template: ReportTemplate) -> str:
    """Serialisasi profil ke JSON rapi (siap dibagikan/diunduh)."""
    return json.dumps(template_to_dict(template), indent=2, ensure_ascii=False) + "\n"


def template_from_json(text: str) -> ReportTemplate:
    """Muat profil dari teks JSON."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON tidak valid: {exc}") from exc
    return template_from_dict(data)


def template_from_yaml(text: str) -> ReportTemplate:
    """Muat profil dari teks YAML (butuh pustaka ``pyyaml``)."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - tergantung lingkungan
        raise ValueError(
            "Pemuatan template YAML membutuhkan pustaka 'pyyaml'. "
            "Gunakan berkas JSON, atau install: pip install pyyaml"
        ) from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - pesan bergantung versi
        raise ValueError(f"YAML tidak valid: {exc}") from exc
    return template_from_dict(data)


def load_template_text(text: str, filename: str = "") -> ReportTemplate:
    """Deteksi format dari nama berkas/isi lalu muat profil template."""
    name = (filename or "").strip().lower()
    stripped = (text or "").lstrip()
    looks_json = stripped.startswith("{") or stripped.startswith("[")
    if name.endswith((".yaml", ".yml")):
        return template_from_yaml(text)
    if name.endswith(".json") or looks_json:
        return template_from_json(text)
    return template_from_yaml(text)
