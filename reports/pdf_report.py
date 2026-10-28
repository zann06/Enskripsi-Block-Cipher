"""PDF report builder for CipherLab using ReportLab.

Prinsip penting:

* Laporan dibangun **hanya** dari data eksekusi aktual
  (:class:`crypto.results.ModeResult`) yang disimpan UI di session state.
  Builder ini tidak pernah mengarang ciphertext, trace, atau status.
* Mode yang belum dijalankan ditandai "Belum dijalankan" secara eksplisit.
* Verifikasi yang gagal ditampilkan "GAGAL" dan tidak pernah ditulis ulang
  sebagai keberhasilan.
* PDF dibuat sepenuhnya lokal; tidak ada API atau layanan eksternal.

Layout: A4, latar putih, aksen navy/violet/cyan secukupnya, tabel dengan
sel Paragraph sehingga teks panjang membungkus dan header tabel berulang
saat tabel menerus ke halaman berikutnya.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from crypto.encoding import display_text, format_bin, format_hex, int16_to_bin, int16_to_hex
from crypto.feistel16 import BLOCK_BITS, BLOCK_BYTES, ROUNDS, key_schedule
from crypto.pipeline import SUPPORTED_MODES, normalize_mode
from crypto.results import ModeResult

__all__ = [
    "Member",
    "ReportLabMissingError",
    "ReportMetadata",
    "build_pdf_bytes",
    "default_filename",
    "resolve_filename",
    "sanitize_filename",
]

_CIPHER_NAME = "Feistel 16-bit (toy, edukasional)"
_ROUNDS_TEXT = str(ROUNDS)
_DISCLAIMER = (
    "Cipher inti CipherLab adalah toy Feistel 16-bit untuk pembelajaran. "
    "Bukan AES dan tidak boleh dipakai untuk data nyata."
)


class ReportLabMissingError(RuntimeError):
    """Raised saat pustaka reportlab belum terpasang.

    Pesannya berisi instruksi instalasi yang jelas; aplikasi sengaja
    **tidak** membuat file pengganti/palsu.
    """

    def __init__(self) -> None:
        super().__init__(
            "Pustaka 'reportlab' belum terpasang sehingga PDF tidak dapat dibuat. "
            "Install terlebih dahulu dengan: pip install reportlab"
        )


# ---------------------------------------------------------------------------
# Metadata laporan
# ---------------------------------------------------------------------------


@dataclass
class Member:
    """Satu anggota kelompok; nama wajib, NIM opsional."""

    name: str
    nim: str = ""


@dataclass
class ReportMetadata:
    """Identitas laporan yang diisi pengguna (tidak ada yang di-hardcode)."""

    title: str = ""
    group_name: str = ""
    course: str = ""
    lecturer: str = ""
    class_name: str = ""
    members: list[Member] = field(default_factory=list)
    report_date: str = ""
    notes: str = ""
    filename: str = ""

    def validate(self) -> None:
        """Validasi minimum sebelum PDF dibuat."""
        if not self.title.strip():
            raise ValueError("Judul laporan wajib diisi.")
        if not self.group_name.strip():
            raise ValueError("Nama kelompok wajib diisi.")
        for index, member in enumerate(self.members, start=1):
            if not member.name.strip() and member.nim.strip():
                raise ValueError(
                    f"Anggota #{index} memiliki NIM tanpa nama. "
                    "Nama anggota wajib diisi; NIM bersifat opsional."
                )


# ---------------------------------------------------------------------------
# Nama file
# ---------------------------------------------------------------------------

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """Ubah teks bebas menjadi nama file yang aman untuk sistem file.

    Karakter tidak aman diganti ``_``, spasi menjadi ``_``, titik/spasi di
    ujung dibuang, panjang dibatasi, dan nama cadangan Windows diawali
    prefix. Jika hasilnya kosong, memakai default ``Laporan_CipherLab``.
    """
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", str(name))
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    cleaned = re.sub(r"_{2,}", "_", cleaned)
    cleaned = cleaned.strip("._ ")
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip("._ ")
    if not cleaned:
        return "Laporan_CipherLab"
    if cleaned.upper() in _WINDOWS_RESERVED:
        cleaned = f"Laporan_{cleaned}"
    return cleaned


def default_filename(group_name: str = "", title: str = "") -> str:
    """Nama file bawaan: ``Laporan_CipherLab_<NamaKelompok>``."""
    base = (group_name or "").strip() or (title or "").strip()
    if not base:
        return "Laporan_CipherLab"
    return f"Laporan_CipherLab_{sanitize_filename(base)}"


def resolve_filename(metadata: ReportMetadata) -> str:
    """Nama file final: milik pengguna bila diisi, selanjutnya disanitasi."""
    chosen = (metadata.filename or "").strip()
    if not chosen:
        chosen = default_filename(metadata.group_name, metadata.title)
    return sanitize_filename(chosen)


# ---------------------------------------------------------------------------
# Utilitas teks untuk Paragraph (ReportLab mem-parsing XML)
# ---------------------------------------------------------------------------

# Simbol tanpa glif pada font bawaan dipetakan ke padanan teks agar PDF
# tidak menampilkan kotak kosong atau gagal render.
_GLYPH_MAP = {
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u2022": "-",
    "\u2192": "->",
    "\u2190": "<-",
    "\u2295": "XOR",
    "\u2713": "OK",
    "\u2714": "OK",
    "\u2717": "X",
    "\u2718": "X",
    "\u00a0": " ",
}


def pdf_safe(text: object) -> str:
    """Bersihkan teks dinamis agar aman dirender font bawaan ReportLab."""
    result = str(text) if text is not None else ""
    for source, replacement in _GLYPH_MAP.items():
        result = result.replace(source, replacement)
    result = "".join(
        ch if (ch >= " " or ch == "\n") else "?" for ch in result
    )
    return result


def esc(text: object, line_breaks: bool = False) -> str:
    """Escape teks untuk Paragraph ReportLab (``&<>`` dan karakter khusus)."""
    result = xml_escape(pdf_safe(text))
    if line_breaks:
        result = result.replace("\n", "<br/>")
    return result


def _mono_or_dash(data: bytes | None) -> str:
    return esc(format_hex(data)) if data else "&mdash;"


# ---------------------------------------------------------------------------
# Font & style
# ---------------------------------------------------------------------------

_HELVETICA = {
    "regular": "Helvetica",
    "bold": "Helvetica-Bold",
    "italic": "Helvetica-Oblique",
    "bold_italic": "Helvetica-BoldOblique",
}

_FONT_STATE: dict[str, str] | None = None


def _get_fonts() -> dict[str, str]:
    """Daftarkan font Bitstream Vera bawaan ReportLab sekali; fallback Helvetica.

    Vera memberi cakupan Latin yang lebih luas (mis. nama dengan aksen)
    dibanding Helvetica Type1.
    """
    global _FONT_STATE
    if _FONT_STATE is not None:
        return _FONT_STATE
    try:
        import reportlab
        from reportlab.lib.fonts import addMapping
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        fonts_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        files = {
            "regular": "Vera.ttf",
            "bold": "VeraBd.ttf",
            "italic": "VeraIt.ttf",
            "bold_italic": "VeraBI.ttf",
        }
        registered: dict[str, str] = {}
        for style, filename in files.items():
            path = os.path.join(fonts_dir, filename)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            pdfmetrics.registerFont(TTFont(f"CipherLab-{style}", path))
            registered[style] = f"CipherLab-{style}"
        addMapping("CipherLab", 0, 0, registered["regular"])
        addMapping("CipherLab", 0, 1, registered["italic"])
        addMapping("CipherLab", 1, 0, registered["bold"])
        addMapping("CipherLab", 1, 1, registered["bold_italic"])
        _FONT_STATE = registered
    except Exception:
        _FONT_STATE = dict(_HELVETICA)
    return _FONT_STATE


# Design tokens (versi terang untuk dokumen cetak)
NAVY = "#0F1B33"
VIOLET = "#8B5CF6"
VIOLET_DARK = "#6D28D9"
CYAN = "#0891B2"
TEXT = "#111827"
MUTED = "#64748B"
BORDER = "#CBD5E1"
ZEBRA = "#F6F8FC"
SUCCESS = "#15803D"
DANGER = "#B91C1C"
WARNING_BG = "#FEF3C7"
WARNING_BORDER = "#D97706"
INFO_BG = "#EEF2FF"
INFO_BORDER = "#8B5CF6"


def _status_markup(verified: bool | None) -> str:
    """Markup status verifikasi; ``None`` berarti belum ada data."""
    if verified is None:
        return esc("Belum dijalankan")
    if verified:
        return f'<font color="{SUCCESS}"><b>BERHASIL</b></font>'
    return f'<font color="{DANGER}"><b>GAGAL</b></font>'


def _content_width() -> float:
    """Lebar efektif konten: A4 dikurangi margin dokumen (45pt per sisi)."""
    from reportlab.lib.pagesizes import A4

    return A4[0] - 90


def _styles() -> dict:
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    f = _get_fonts()
    return {
        "title": ParagraphStyle(
            "title", fontName=f["bold"], fontSize=21, leading=26,
            textColor=NAVY, alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=f["regular"], fontSize=11.5, leading=15,
            textColor=CYAN, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1", fontName=f["bold"], fontSize=13.5, leading=17,
            textColor=NAVY, spaceBefore=16, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2", fontName=f["bold"], fontSize=11, leading=14,
            textColor=VIOLET_DARK, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", fontSize=9.8, leading=13.5, textColor=TEXT, spaceAfter=4,
            **{"fontName": f["regular"]},
        ),
        "muted": ParagraphStyle(
            "muted", fontSize=8.3, leading=11, textColor=MUTED,
            fontName=f["italic"],
        ),
        "cell": ParagraphStyle(
            "cell", fontSize=8.8, leading=11.5, textColor=TEXT,
            fontName=f["regular"],
        ),
        "cell_mono": ParagraphStyle(
            "cell_mono", fontSize=7.6, leading=9.8, textColor=TEXT,
            fontName="Courier",
        ),
        "cell_head": ParagraphStyle(
            "cell_head", fontSize=8.4, leading=10.5,
            textColor="#FFFFFF", fontName=f["bold"],
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontSize=10.5, leading=16, textColor=TEXT,
            fontName=f["regular"], alignment=TA_CENTER,
        ),
    }


def _base_table_style() -> list[tuple]:
    return [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), "#FFFFFF"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), ["#FFFFFF", ZEBRA]),
    ]


def _callout(story: list, styles: dict, text: str, bg: str, border: str) -> None:
    """Kotak info/peringatan satu sel selebar konten."""
    from reportlab.platypus import Paragraph, Table

    table = Table(
        [[Paragraph(text, styles["body"])]],
        colWidths=[_content_width()],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 0.8, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ],
    )
    story.append(table)
    story.append(_spacer(6))


def _spacer(height: float):
    from reportlab.platypus import Spacer

    return Spacer(1, height)


# ---------------------------------------------------------------------------
# Normalisasi hasil eksekusi
# ---------------------------------------------------------------------------


def _as_result_map(results) -> dict[str, ModeResult]:
    """Terima ``None``, list, atau dict hasil; kembalikan dict per mode."""
    mapping: dict[str, ModeResult] = {}
    if results is None:
        return mapping
    if isinstance(results, ModeResult):
        results = [results]
    items = results.items() if isinstance(results, dict) else enumerate(results)
    for _key, result in items:
        if result is None:
            continue
        mapping[normalize_mode(result.mode)] = result
    return mapping


def _clean_members(metadata: ReportMetadata) -> list[Member]:
    """Buang baris anggota yang benar-benar kosong; tolak NIM tanpa nama."""
    cleaned: list[Member] = []
    for index, member in enumerate(metadata.members, start=1):
        name = member.name.strip()
        nim = member.nim.strip()
        if not name and not nim:
            continue
        if not name and nim:
            raise ValueError(
                f"Anggota #{index} memiliki NIM tanpa nama. "
                "Nama anggota wajib diisi; NIM bersifat opsional."
            )
        cleaned.append(Member(name=name, nim=nim))
    return cleaned


def _repeat_stats(blocks) -> tuple[int, bool]:
    """Statistik blok berulang dari data aktual.

    Mengembalikan ``(jumlah_blok_plaintext_yang_berulang, ciphertext_juga_identik)``.
    """
    plain_counts = Counter(block.plaintext_block for block in blocks)
    repeated = sum(count - 1 for count in plain_counts.values() if count > 1)
    if repeated == 0:
        return 0, False
    identical = all(
        len({b.ciphertext_block for b in blocks if b.plaintext_block == value}) == 1
        for value, count in plain_counts.items()
        if count > 1
    )
    return repeated, identical


# ---------------------------------------------------------------------------
# Temuan & kesimpulan (semua kalimat bersyarat pada data aktual)
# ---------------------------------------------------------------------------


def build_findings(result_map: dict[str, ModeResult]) -> list[str]:
    """Susun daftar temuan faktual dari hasil eksekusi; tanpa mengarang."""
    findings: list[str] = []
    executed = [mode for mode in SUPPORTED_MODES if mode in result_map]
    verified = [mode for mode in executed if result_map[mode].verified]

    if not executed:
        findings.append(
            "Belum ada mode yang dijalankan, sehingga laporan ini belum memuat "
            "hasil eksekusi dan belum dapat menarik kesimpulan."
        )
        return findings

    findings.append(
        f"Dari 3 mode yang dispecifikasikan (ECB, CBC, CTR), {len(executed)} mode "
        f"dijalankan dan {len(verified)} di antaranya lolos verifikasi dekripsi."
    )

    for mode in SUPPORTED_MODES:
        result = result_map.get(mode)
        if result is None:
            findings.append(f"Mode {mode} belum dijalankan; tidak ada kesimpulan untuk mode ini.")
            continue
        if result.verified:
            findings.append(
                f"Round-trip {mode} BERHASIL pada input uji ini: dekripsi menghasilkan "
                f"kembali {len(result.plaintext_bytes)} byte plaintext asli "
                f"({result.block_count} blok ciphertext)."
            )
        elif result.decryption_error:
            findings.append(
                f"Round-trip {mode} GAGAL: dekripsi menghasilkan error ({result.decryption_error}). "
                "Kesimpulan keberhasilan tidak dapat diberikan untuk mode ini."
            )
        else:
            findings.append(
                f"Round-trip {mode} GAGAL: hasil dekripsi tidak identik dengan plaintext asli. "
                "Kesimpulan keberhasilan tidak dapat diberikan untuk mode ini."
            )

    ecb = result_map.get("ECB")
    if ecb is not None and ecb.blocks:
        repeated, identical = _repeat_stats(ecb.blocks)
        if repeated:
            if identical:
                findings.append(
                    f"Pada ECB teramati {repeated} blok plaintext yang berulang dan "
                    "menghasilkan blok ciphertext yang identik; pola khas ECB ini "
                    "berasal dari data eksekusi, bukan ilustrasi."
                )
            else:
                findings.append(
                    f"Pada ECB teramati {repeated} blok plaintext berulang namun "
                    "ciphertext-nya berbeda; temuan ini tidak sesuai karakteristik ECB "
                    "dan layak ditelusuri lebih lanjut."
                )
        else:
            findings.append(
                "Input ECB pada eksekusi ini tidak memiliki blok plaintext berulang, "
                "sehingga pengulangan pola ECB tidak teramati pada data ini."
            )

    cbc = result_map.get("CBC")
    if cbc is not None and cbc.blocks:
        repeated, identical = _repeat_stats(cbc.blocks)
        if repeated and not identical:
            findings.append(
                f"Pada CBC, {repeated} blok plaintext berulang tetap menghasilkan "
                "ciphertext berbeda karena chaining dengan IV/ciphertext sebelumnya "
                "(teramati pada data eksekusi)."
            )
        elif repeated and identical:
            findings.append(
                f"Pada CBC teramati {repeated} blok plaintext berulang yang menghasilkan "
                "ciphertext identik; pada CBC kondisi ini hanya terjadi bila rantai "
                "sebelumnya juga identik."
            )

    ctr = result_map.get("CTR")
    if ctr is not None:
        findings.append(
            f"CTR mempertahankan panjang data: ciphertext {len(ctr.ciphertext)} byte "
            f"untuk plaintext {len(ctr.plaintext_bytes)} byte (tanpa padding)."
        )

    return findings


# ---------------------------------------------------------------------------
# Bagian-bagian PDF
# ---------------------------------------------------------------------------


def _cover(story: list, styles: dict, metadata: ReportMetadata, generated_at: datetime) -> None:
    from reportlab.platypus import PageBreak, Paragraph, Table

    story.append(_spacer(56))
    story.append(Paragraph(esc(metadata.title), styles["title"]))
    story.append(_spacer(8))
    story.append(
        Paragraph("CipherLab - Block Cipher 16-bit (ECB, CBC, CTR) untuk Edukasi", styles["subtitle"])
    )
    story.append(_spacer(26))

    rows: list[list[str]] = []
    rows.append(["Kelompok", esc(metadata.group_name)])
    if metadata.course.strip():
        rows.append(["Mata Kuliah", esc(metadata.course)])
    if metadata.lecturer.strip():
        rows.append(["Dosen", esc(metadata.lecturer)])
    if metadata.class_name.strip():
        rows.append(["Kelas", esc(metadata.class_name)])
    if metadata.report_date.strip():
        rows.append(["Tanggal Laporan", esc(metadata.report_date)])
    meta_table = Table(
        [[Paragraph(f"<b>{label}</b>", styles["cell"]), Paragraph(value, styles["cell"])] for label, value in rows],
        colWidths=[110, None],
        style=[
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("BACKGROUND", (0, 0), (0, -1), ZEBRA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ],
    )
    story.append(meta_table)
    story.append(_spacer(18))

    members = _clean_members(metadata)
    if members:
        story.append(Paragraph("Anggota Kelompok", styles["h2"]))
        member_rows = [
            [
                Paragraph("No", styles["cell_head"]),
                Paragraph("Nama", styles["cell_head"]),
                Paragraph("NIM", styles["cell_head"]),
            ]
        ]
        for index, member in enumerate(members, start=1):
            member_rows.append(
                [
                    Paragraph(str(index), styles["cell"]),
                    Paragraph(esc(member.name), styles["cell"]),
                    Paragraph(esc(member.nim) if member.nim else "-", styles["cell"]),
                ]
            )
        story.append(
            Table(
                member_rows,
                colWidths=[36, None, 130],
                repeatRows=1,
                style=_base_table_style(),
            )
        )
        story.append(_spacer(18))

    _callout(
        story, styles,
        f"<b>Peringatan:</b> {_DISCLAIMER} Seluruh hasil pada laporan ini berasal dari "
        "eksekusi aktual aplikasi pada parameter uji yang dimasukkan pengguna.",
        WARNING_BG, WARNING_BORDER,
    )
    story.append(
        Paragraph(
            f"Laporan dibuat otomatis oleh CipherLab pada {esc(generated_at.strftime('%d/%m/%Y %H:%M:%S %Z'))} "
            "(lokal, tanpa layanan eksternal).",
            styles["muted"],
        )
    )
    story.append(PageBreak())


def _summary_section(story: list, styles: dict, result_map: dict[str, ModeResult], generated_at: datetime) -> None:
    from reportlab.platypus import Paragraph, Table

    story.append(Paragraph("1. Ringkasan Eksekusi", styles["h1"]))
    executed = [mode for mode in SUPPORTED_MODES if mode in result_map]
    verified = [mode for mode in executed if result_map[mode].verified]
    story.append(
        Paragraph(
            esc(
                f"Laporan ini mendokumentasikan {len(executed)} dari 3 mode operasi "
                f"yang dijalankan pada sesi aplikasi ({', '.join(executed) if executed else 'belum ada'}). "
                f"Verifikasi dekripsi (round-trip) BERHASIL untuk {len(verified)} mode."
            ),
            styles["body"],
        )
    )

    spec_rows = [
        ["Cipher inti", f"{_CIPHER_NAME}, {_ROUNDS_TEXT} ronde"],
        ["Ukuran blok", f"{BLOCK_BITS} bit ({BLOCK_BYTES} byte)"],
        ["Encoding", "UTF-8"],
        ["Padding", "PKCS#7 2 byte (ECB dan CBC); CTR tanpa padding"],
        ["Fungsi ronde", "F(R, k) = ROTL8(SBOX[R XOR k], 1)"],
        ["Waktu laporan dibuat", esc(generated_at.strftime("%d/%m/%Y %H:%M:%S %Z"))],
    ]
    story.append(
        Table(
            [
                [Paragraph(f"<b>{esc(label)}</b>", styles["cell"]), Paragraph(esc(value), styles["cell"])]
                for label, value in spec_rows
            ],
            colWidths=[130, None],
            style=[
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("BACKGROUND", (0, 0), (0, -1), ZEBRA),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ],
        )
    )
    story.append(_spacer(10))

    head = [Paragraph(esc(t), styles["cell_head"]) for t in
            ["Mode", "Status Eksekusi", "Verifikasi Dekripsi", "Jumlah Blok", "Ciphertext (byte)"]]
    body_rows = [head]
    for mode in SUPPORTED_MODES:
        result = result_map.get(mode)
        if result is None:
            body_rows.append(
                [
                    Paragraph(f"<b>{mode}</b>", styles["cell"]),
                    Paragraph(esc("Belum dijalankan"), styles["cell"]),
                    Paragraph(_status_markup(None), styles["cell"]),
                    Paragraph("-", styles["cell"]),
                    Paragraph("-", styles["cell"]),
                ]
            )
        else:
            body_rows.append(
                [
                    Paragraph(f"<b>{mode}</b>", styles["cell"]),
                    Paragraph(
                        esc(f"Dijalankan {result.executed_at.strftime('%d/%m/%Y %H:%M:%S')}"),
                        styles["cell"],
                    ),
                    Paragraph(_status_markup(result.verified), styles["cell"]),
                    Paragraph(str(result.block_count), styles["cell"]),
                    Paragraph(str(result.ciphertext_length), styles["cell"]),
                ]
            )
    story.append(Table(body_rows, repeatRows=1, style=_base_table_style(), colWidths=[52, 120, 105, 62, 80]))


def _purpose_section(story: list, styles: dict, result_map: dict[str, ModeResult]) -> None:
    from reportlab.platypus import Paragraph

    story.append(Paragraph("2. Tujuan dan Ruang Lingkup", styles["h1"]))
    story.append(
        Paragraph(
            esc(
                "Laporan ini dibuat untuk mendokumentasikan hasil eksekusi enkripsi dan dekripsi "
                "block cipher 16-bit pada mode ECB, CBC, dan CTR sebagaimana dijalankan di aplikasi "
                "CipherLab. Setiap angka, tabel blok, trace, dan status verifikasi diambil dari objek "
                "hasil eksekusi yang sama dengan yang ditampilkan pada antarmuka aplikasi."
            ),
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            esc(
                "Ruang lingkup: parameter uji yang dipilih pengguna, hasil per blok (HEX dan BIN), "
                "trace perhitungan yang tersedia dari implementasi, hasil dekripsi, serta verifikasi "
                "round-trip per mode. Laporan tidak memuat klaim keamanan kriptografis; pembatasan "
                "dibahas pada bagian Batasan."
            ),
            styles["body"],
        )
    )


def _algorithm_section(story: list, styles: dict) -> None:
    from reportlab.platypus import Paragraph

    story.append(Paragraph("3. Algoritma dan Rumus Mode", styles["h1"]))
    story.append(
        Paragraph(
            esc(
                f"Cipher inti adalah toy Feistel network 16-bit dengan {_ROUNDS_TEXT} ronde. Blok 16 bit "
                "dipecah menjadi dua half 8 bit (L, R). Fungsi ronde F(R, k) = ROTL8(SBOX[R XOR k], 1) "
                "dengan SBOX berupa permutasi 256 byte tetap yang terdokumentasi. Key schedule memutar "
                "kunci 16 bit sebesar 3*i bit per ronde, mencampur kedua byte dengan konstanta ronde, "
                "lalu melewatkannya melalui SBOX sehingga menghasilkan 8 kunci ronde 8 bit. Enkripsi dan "
                "dekripsi saling invers; dekripsi menjalankan ronde terbalik dengan update (L, R) <- "
                "(R XOR F(L, k), L). Algoritma ini hanya untuk pembelajaran."
            ),
            styles["body"],
        )
    )

    formulas = [
        ("ECB", "C<sub>i</sub> = E<sub>K</sub>(P<sub>i</sub>)", "P<sub>i</sub> = D<sub>K</sub>(C<sub>i</sub>)",
         "Setiap blok diproses independen; tidak menggunakan IV."),
        ("CBC", "C<sub>i</sub> = E<sub>K</sub>(P<sub>i</sub> XOR C<sub>i-1</sub>), C<sub>0</sub> = IV",
         "P<sub>i</sub> = D<sub>K</sub>(C<sub>i</sub>) XOR C<sub>i-1</sub>",
         "Chaining: tiap blok ciphertext bergantung pada blok sebelumnya."),
        ("CTR", "S<sub>i</sub> = E<sub>K</sub>(T<sub>i</sub>); C<sub>i</sub> = P<sub>i</sub> XOR S<sub>i</sub>",
         "P<sub>i</sub> = C<sub>i</sub> XOR S<sub>i</sub>",
         "T<sub>i</sub> = counter awal + i (tanpa wrap melewati 0xFFFF); tanpa padding."),
    ]
    head = [Paragraph(esc(t), styles["cell_head"]) for t in ["Mode", "Enkripsi", "Dekripsi", "Catatan"]]
    rows = [head]
    for mode, enc, dec, note in formulas:
        rows.append(
            [
                Paragraph(f"<b>{mode}</b>", styles["cell"]),
                Paragraph(enc, styles["cell"]),
                Paragraph(dec, styles["cell"]),
                Paragraph(esc(note), styles["cell"]),
            ]
        )
    from reportlab.platypus import Table

    story.append(Table(rows, repeatRows=1, style=_base_table_style(), colWidths=[38, None, None, 150]))


def _param_row(styles: dict, label: str, value_markup: str) -> list:
    from reportlab.platypus import Paragraph

    return [
        Paragraph(f"<b>{esc(label)}</b>", styles["cell"]),
        Paragraph(value_markup, styles["cell"]),
    ]


def _mode_section(story: list, styles: dict, mode: str, result: ModeResult | None,
                  include_traces: bool) -> None:
    from reportlab.platypus import Paragraph, Table

    section_number = {"ECB": 4, "CBC": 5, "CTR": 6}[mode]
    story.append(Paragraph(f"{section_number}. Mode {mode}", styles["h1"]))

    if result is None:
        _callout(
            story, styles,
            f"<b>Belum dijalankan.</b> Mode {mode} belum pernah dieksekusi pada sesi ini, "
            f"sehingga tidak ada parameter, tabel blok, trace, atau status verifikasi yang dapat "
            f"disajikan untuk mode ini. Laporan tidak membuat data contoh; jalankan mode {mode} "
            "pada halaman Playground untuk memasukkan hasilnya ke laporan.",
            INFO_BG, INFO_BORDER,
        )
        return

    story.append(Paragraph(esc(result.mode_label), styles["h2"]))

    param_rows = [
        _param_row(styles, "Waktu eksekusi", esc(result.executed_at.strftime("%d/%m/%Y %H:%M:%S %Z"))),
        _param_row(
            styles, "Plaintext (teks)",
            esc(display_text(result.plaintext_text, limit=2000))
            if result.plaintext_text
            else "(kosong)",
        ),
        _param_row(styles, "Panjang plaintext", f"{len(result.plaintext_bytes)} byte (encoding {esc(result.encoding)})"),
        _param_row(
            styles, "Kunci",
            f'<font face="Courier">0x{esc(int16_to_hex(result.key))} / {esc(int16_to_bin(result.key))}</font>',
        ),
    ]
    if mode == "CBC":
        param_rows.append(
            _param_row(
                styles, "IV",
                f'<font face="Courier">0x{esc(int16_to_hex(result.iv))} / {esc(int16_to_bin(result.iv))}</font>',
            )
        )
    if mode == "CTR":
        param_rows.append(
            _param_row(
                styles, "Counter awal",
                f'<font face="Courier">0x{esc(int16_to_hex(result.initial_counter))} / '
                f'{esc(int16_to_bin(result.initial_counter))}</font>',
            )
        )
        param_rows.append(_param_row(styles, "Aturan counter", "T_i = counter awal + i; increment +1, tanpa wrap"))
    if result.padding:
        param_rows.append(_param_row(styles, "Padding", esc(result.padding)))
    else:
        param_rows.append(_param_row(styles, "Padding", "Tidak digunakan (panjang dipertahankan)"))
    param_rows.append(_param_row(styles, "Jumlah blok", str(result.block_count)))
    param_rows.append(_param_row(styles, "Panjang ciphertext", f"{result.ciphertext_length} byte"))
    param_rows.append(
        _param_row(
            styles, "Status verifikasi",
            f"{_status_markup(result.verified)} (dekripsi round-trip terhadap plaintext asli)",
        )
    )
    story.append(
        Table(param_rows, colWidths=[120, None], style=[
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("BACKGROUND", (0, 0), (0, -1), ZEBRA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(_spacer(8))

    story.append(Paragraph("Hasil dekripsi", styles["h2"]))
    if result.decryption_error:
        story.append(
            Paragraph(
                f'<font color="{DANGER}"><b>Dekripsi menghasilkan error:</b></font> '
                f"{esc(result.decryption_error)}",
                styles["body"],
            )
        )
    else:
        story.append(
            Paragraph(
                esc(display_text(result.decrypted_text, limit=2000)) if result.decrypted_text else "(kosong)",
                styles["body"],
            )
        )
    if result.verified:
        story.append(
            Paragraph(
                f'<font color="{SUCCESS}"><b>Verifikasi BERHASIL</b></font> - hasil dekripsi identik '
                "byte-per-byte dengan plaintext asli.",
                styles["body"],
            )
        )
    else:
        story.append(
            Paragraph(
                f'<font color="{DANGER}"><b>Verifikasi GAGAL</b></font> - hasil dekripsi TIDAK identik '
                "dengan plaintext asli. Jangan menuliskan mode ini sebagai round-trip yang berhasil.",
                styles["body"],
            )
        )

    story.append(Paragraph("Tabel blok", styles["h2"]))
    if not result.blocks:
        story.append(
            Paragraph(
                esc(
                    "Plaintext kosong dan mode ini tidak menghasilkan blok yang diproses; "
                    "ciphertext kosong. (ECB/CBC tetap menghasilkan satu blok padding; CTR tidak.)"
                ),
                styles["body"],
            )
        )
    else:
        story.append(_block_table(styles, mode, result))

    if result.blocks and result.blocks[0].feistel_rounds:
        story.append(Paragraph("Trace ronde Feistel (enkripsi) - Blok 1", styles["h2"]))
        story.append(_round_trace_table(styles, result.blocks[0].feistel_rounds))
        if include_traces:
            story.append(
                Paragraph("Trace blok lainnya tersedia pada Lampiran A.", styles["muted"])
            )
        else:
            story.append(
                Paragraph(
                    "Lampiran trace lengkap dinonaktifkan saat laporan ini dibuat; hanya trace "
                    "Blok 1 yang disertakan.",
                    styles["muted"],
                )
            )


def _block_table(styles: dict, mode: str, result: ModeResult):
    from reportlab.platypus import Paragraph, Table

    headers = ["Blok", "Plaintext HEX", "Plaintext BIN"]
    if mode == "ECB":
        headers += ["Ciphertext HEX", "Ciphertext BIN"]
        widths = [30, 62, 118, 62, 118]
    elif mode == "CBC":
        headers += ["XOR dgn (IV/C prev)", "Input Feistel", "Ciphertext HEX", "Ciphertext BIN"]
        widths = [26, 56, 84, 56, 56, 56, 84]
    else:  # CTR
        headers += ["Counter", "Keystream", "Ciphertext HEX", "Ciphertext BIN"]
        widths = [26, 56, 84, 48, 56, 56, 84]

    rows = [[Paragraph(esc(h), styles["cell_head"]) for h in headers]]
    for block in result.blocks:
        row = [
            Paragraph(str(block.number), styles["cell"]),
            Paragraph(esc(format_hex(block.plaintext_block)), styles["cell_mono"]),
            Paragraph(esc(format_bin(block.plaintext_block)), styles["cell_mono"]),
        ]
        if mode == "CBC":
            row += [
                Paragraph(_mono_or_dash(block.xor_value), styles["cell_mono"]),
                Paragraph(esc(format_hex(block.feistel_input)), styles["cell_mono"]),
                Paragraph(esc(format_hex(block.ciphertext_block)), styles["cell_mono"]),
                Paragraph(esc(format_bin(block.ciphertext_block)), styles["cell_mono"]),
            ]
        elif mode == "CTR":
            row += [
                Paragraph(_mono_or_dash(block.counter_block), styles["cell_mono"]),
                Paragraph(_mono_or_dash(block.keystream), styles["cell_mono"]),
                Paragraph(esc(format_hex(block.ciphertext_block)), styles["cell_mono"]),
                Paragraph(esc(format_bin(block.ciphertext_block)), styles["cell_mono"]),
            ]
        else:
            row += [
                Paragraph(esc(format_hex(block.ciphertext_block)), styles["cell_mono"]),
                Paragraph(esc(format_bin(block.ciphertext_block)), styles["cell_mono"]),
            ]
        rows.append(row)

    usable_width = _content_width()
    scale = min(1.0, usable_width / sum(widths))
    widths = [w * scale for w in widths]
    return Table(rows, colWidths=widths, repeatRows=1, style=_base_table_style())


def _round_trace_table(styles: dict, rounds: list):
    from reportlab.platypus import Paragraph, Table

    headers = ["Ronde", "L masuk", "R masuk", "K ronde", "F(R, K)", "L keluar", "R keluar"]
    rows = [[Paragraph(esc(h), styles["cell_head"]) for h in headers]]
    for trace in rounds:
        rows.append(
            [
                Paragraph(str(trace.round_number), styles["cell"]),
                Paragraph(f"{trace.left_in:02X}", styles["cell_mono"]),
                Paragraph(f"{trace.right_in:02X}", styles["cell_mono"]),
                Paragraph(f"{trace.round_key:02X}", styles["cell_mono"]),
                Paragraph(f"{trace.f_output:02X}", styles["cell_mono"]),
                Paragraph(f"{trace.left_out:02X}", styles["cell_mono"]),
                Paragraph(f"{trace.right_out:02X}", styles["cell_mono"]),
            ]
        )
    widths = [34, 44, 44, 44, 44, 44, 44]
    return Table(rows, colWidths=widths, repeatRows=1, style=_base_table_style())


def _comparison_section(story: list, styles: dict, result_map: dict[str, ModeResult]) -> None:
    from reportlab.platypus import Paragraph, Table

    story.append(Paragraph("7. Perbandingan Mode", styles["h1"]))

    def cell(mode: str, text: str, mono: bool = False, markup: str | None = None) -> Paragraph:
        if markup is not None:
            return Paragraph(markup, styles["cell"])
        return Paragraph(esc(text) if not mono else text, styles["cell_mono"] if mono else styles["cell"])

    def actual(mode: str, result: ModeResult | None, formatter) -> str:
        if result is None:
            return "-"
        return formatter(result)

    rows = [
        ["Rumus enkripsi", "C_i = E_K(P_i)", "C_i = E_K(P_i XOR C_i-1)", "C_i = P_i XOR E_K(T_i)"],
        ["Rumus dekripsi", "P_i = D_K(C_i)", "P_i = D_K(C_i) XOR C_i-1", "P_i = C_i XOR E_K(T_i)"],
        ["IV / counter", "Tidak digunakan", "IV 16-bit (C_0 = IV)", "Counter awal 16-bit, increment +1"],
        ["Padding", "PKCS#7 2 byte", "PKCS#7 2 byte", "Tanpa padding"],
        ["Dependensi antarblok", "Independen", "Bergantung blok sebelumnya", "Melalui counter/keystream"],
    ]
    head = [Paragraph(esc("Aspek"), styles["cell_head"])] + [
        Paragraph(esc(m), styles["cell_head"]) for m in SUPPORTED_MODES
    ]
    table_rows = [head]
    for aspect, ecb, cbc, ctr in rows:
        table_rows.append(
            [
                Paragraph(f"<b>{esc(aspect)}</b>", styles["cell"]),
                cell("ECB", ecb, mono=True),
                cell("CBC", cbc, mono=True),
                cell("CTR", ctr, mono=True),
            ]
        )

    observed_label = "Dari eksekusi aktual pada laporan ini"
    table_rows.append(
        [
            Paragraph(f"<b>Status eksekusi</b><br/><font size='6.5' color='{MUTED}'>{observed_label}</font>", styles["cell"]),
            *[Paragraph(esc("Dijalankan" if m in result_map else "Belum dijalankan"), styles["cell"]) for m in SUPPORTED_MODES],
        ]
    )
    table_rows.append(
        [
            Paragraph("<b>Verifikasi</b>", styles["cell"]),
            *[Paragraph(_status_markup(result_map[m].verified if m in result_map else None), styles["cell"])
              for m in SUPPORTED_MODES],
        ]
    )
    table_rows.append(
        [
            Paragraph("<b>Jumlah blok</b>", styles["cell"]),
            *[Paragraph(actual(m, result_map.get(m), lambda r: str(r.block_count)), styles["cell"])
              for m in SUPPORTED_MODES],
        ]
    )
    table_rows.append(
        [
            Paragraph("<b>Panjang ciphertext (byte)</b>", styles["cell"]),
            *[Paragraph(actual(m, result_map.get(m), lambda r: str(r.ciphertext_length)), styles["cell"])
              for m in SUPPORTED_MODES],
        ]
    )

    def repeat_text(mode: str) -> str:
        result = result_map.get(mode)
        if result is None or not result.blocks:
            return "-"
        repeated, identical = _repeat_stats(result.blocks)
        if not repeated:
            return "Tidak ada blok plaintext berulang"
        return f"{repeated} blok berulang; ciphertext {'identik' if identical else 'berbeda'}"

    table_rows.append(
        [
            Paragraph("<b>Blok plaintext berulang</b>", styles["cell"]),
            *[Paragraph(esc(repeat_text(m)), styles["cell"]) for m in SUPPORTED_MODES],
        ]
    )

    from reportlab.platypus import Table

    story.append(
        Table(table_rows, colWidths=[120, None, None, None], repeatRows=1, style=_base_table_style())
    )
    story.append(
        Paragraph(
            "Baris Status eksekusi, Verifikasi, Jumlah blok, Panjang ciphertext, dan Blok "
            "berulang dihitung dari hasil eksekusi aktual pada sesi ini; baris lainnya adalah "
            "spesifikasi mode. Tanda '-' berarti tidak ada data karena mode belum dijalankan.",
            styles["muted"],
        )
    )


def _conclusion_section(story: list, styles: dict, result_map: dict[str, ModeResult],
                        metadata: ReportMetadata) -> None:
    from reportlab.platypus import Paragraph

    story.append(Paragraph("8. Analisis dan Kesimpulan", styles["h1"]))
    story.append(
        Paragraph(
            esc(
                "Kesimpulan berikut disusun hanya dari data eksekusi aktual pada laporan ini. "
                "Tidak ada temuan yang ditambahkan di luar data tersebut."
            ),
            styles["body"],
        )
    )
    for finding in build_findings(result_map):
        story.append(Paragraph(esc("- " + finding), styles["body"]))
    if metadata.notes.strip():
        story.append(Paragraph("<b>Catatan kelompok</b>", styles["h2"]))
        story.append(Paragraph(esc(metadata.notes, line_breaks=True), styles["body"]))


def _limitations_section(story: list, styles: dict) -> None:
    from reportlab.platypus import Paragraph

    story.append(Paragraph("9. Batasan dan Peringatan Keamanan", styles["h1"]))
    limitations = [
        "Toy Feistel 16-bit hanya alat pembelajaran: blok dan kunci 16 bit terlalu kecil dan "
        "sangat rentan brute force. Algoritma ini bukan AES dan tidak boleh dipakai untuk data nyata.",
        "Mode ECB tidak menyembunyikan pola plaintext yang berulang.",
        "CBC dan CTR pada laporan ini tidak disertai mekanisme autentikasi (MAC/AEAD), sehingga "
        "integritas ciphertext tidak terjamin.",
        "Pada penggunaan nyata, IV dan nonce/counter harus unik dan dikelola dengan benar; "
        "penggunaan ulang dapat merusak keamanan.",
        "Laporan ini menyimpan parameter uji akademik yang dimasukkan pengguna, termasuk kunci uji, "
        "IV/counter, dan plaintext uji. Jangan memasukkan kunci, password, atau data rahasia nyata.",
    ]
    for item in limitations:
        story.append(Paragraph(esc("- " + item), styles["body"]))


def _appendix(story: list, styles: dict, result_map: dict[str, ModeResult]) -> None:
    from reportlab.platypus import PageBreak, Paragraph

    story.append(PageBreak())
    story.append(Paragraph("Lampiran A. Trace Ronde Feistel Lengkap (Enkripsi)", styles["h1"]))
    traced_modes = [m for m in SUPPORTED_MODES if m in result_map and any(b.feistel_rounds for b in result_map[m].blocks)]
    if not traced_modes:
        story.append(
            Paragraph(
                esc("Tidak ada trace ronde yang tersedia karena belum ada mode yang dijalankan "
                    "dengan opsi trace."),
                styles["body"],
            )
        )
    for mode in traced_modes:
        for block in result_map[mode].blocks:
            if not block.feistel_rounds:
                continue
            story.append(Paragraph(f"{mode} - Blok {block.number} (enkripsi)", styles["h2"]))
            story.append(_round_trace_table(styles, block.feistel_rounds))
            story.append(_spacer(6))

    story.append(Paragraph("Lampiran B. Jadwal Kunci (Key Schedule)", styles["h1"]))
    seen_keys: dict[int, tuple[int, ...]] = {}
    for mode in SUPPORTED_MODES:
        result = result_map.get(mode)
        if result is not None and result.key not in seen_keys:
            seen_keys[result.key] = key_schedule(result.key)
    if not seen_keys:
        story.append(Paragraph(esc("Belum ada eksekusi; jadwal kunci tidak tersedia."), styles["body"]))
    for key, round_keys in seen_keys.items():
        story.append(
            Paragraph(
                f"Kunci 0x{esc(int16_to_hex(key))} ({esc(int16_to_bin(key))}) menghasilkan kunci ronde:",
                styles["body"],
            )
        )
        story.append(
            Paragraph(
                "<font face='Courier'>"
                + esc(", ".join(f"k{i + 1}=0x{rk:02X}" for i, rk in enumerate(round_keys)))
                + "</font>",
                styles["body"],
            )
        )


# ---------------------------------------------------------------------------
# Entry point utama
# ---------------------------------------------------------------------------


def build_pdf_bytes(
    metadata: ReportMetadata,
    results,
    include_traces: bool = True,
    generated_at: datetime | None = None,
) -> bytes:
    """Bangun PDF laporan dari metadata dan hasil eksekusi aktual.

    ``results`` dapat berupa :class:`crypto.results.ModeResult` tunggal,
    list, atau dict ber-key mode. Mode yang tidak ada ditandai "Belum
    dijalankan". Mengembalikan bytes PDF siap diunduh.

    Raises:
        ValueError: bila judul/nama kelompok kosong atau ada NIM tanpa nama.
        ReportLabMissingError: bila pustaka reportlab belum terpasang.
    """
    metadata.validate()
    result_map = _as_result_map(results)
    generated_at = generated_at or datetime.now().astimezone()

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
    except ImportError as exc:  # pragma: no cover - jalur tanpa reportlab
        raise ReportLabMissingError() from exc

    styles = _styles()
    fonts = _get_fonts()
    width, height = A4

    buffer = BytesIO()

    def _footer(canvas, doc, with_number: bool) -> None:
        canvas.saveState()
        canvas.setFont(fonts["italic"], 7.2)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.setStrokeColor(colors.HexColor(BORDER))
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 38, width - doc.leftMargin, 38)
        canvas.drawString(
            doc.leftMargin, 27,
            "CipherLab - laporan dibuat lokal dengan ReportLab; toy cipher 16-bit, bukan untuk data nyata.",
        )
        stamp = f"Dibuat {generated_at.strftime('%d/%m/%Y %H:%M:%S')}"
        if with_number:
            stamp = f"{stamp} - Halaman {canvas.getPageNumber()}"
        canvas.drawRightString(width - doc.leftMargin, 27, stamp)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=48,
        bottomMargin=52,
        title=metadata.title.strip() or "Laporan CipherLab",
        author=metadata.group_name.strip() or "CipherLab",
        subject="Laporan praktikum block cipher 16-bit (ECB, CBC, CTR)",
    )

    story: list = []
    _cover(story, styles, metadata, generated_at)
    _summary_section(story, styles, result_map, generated_at)
    _purpose_section(story, styles, result_map)
    _algorithm_section(story, styles)
    for mode in SUPPORTED_MODES:
        _mode_section(story, styles, mode, result_map.get(mode), include_traces)
    _comparison_section(story, styles, result_map)
    _conclusion_section(story, styles, result_map, metadata)
    _limitations_section(story, styles)
    if include_traces:
        _appendix(story, styles, result_map)

    doc.build(
        story,
        onFirstPage=lambda canvas, doc_: _footer(canvas, doc_, with_number=False),
        onLaterPages=lambda canvas, doc_: _footer(canvas, doc_, with_number=True),
    )
    return buffer.getvalue()
