"""CipherLab reporting package.

Semua nilai laporan diambil dari objek hasil eksekusi aktual
(:class:`crypto.results.ModeResult`); modul di sini tidak pernah membuat
ciphertext, trace, atau status verifikasi sendiri.
"""

from .pdf_report import (
    Member,
    ReportLabMissingError,
    ReportMetadata,
    ReportTemplate,
    build_pdf_bytes,
    default_filename,
    resolve_filename,
    sanitize_filename,
)
from .template import (
    DEFAULT_ACCENT,
    DEFAULT_SECTIONS,
    FONT_LABELS,
    SECTION_KEYS,
    SECTION_LABELS,
    load_template_text,
    template_from_dict,
    template_from_json,
    template_from_yaml,
    template_to_dict,
    template_to_json,
)

__all__ = [
    "DEFAULT_ACCENT",
    "DEFAULT_SECTIONS",
    "FONT_LABELS",
    "Member",
    "ReportLabMissingError",
    "ReportMetadata",
    "ReportTemplate",
    "SECTION_KEYS",
    "SECTION_LABELS",
    "build_pdf_bytes",
    "default_filename",
    "load_template_text",
    "resolve_filename",
    "sanitize_filename",
    "template_from_dict",
    "template_from_json",
    "template_from_yaml",
    "template_to_dict",
    "template_to_json",
]
