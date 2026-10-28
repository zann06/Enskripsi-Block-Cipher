"""Ekspor laporan Markdown dan CSV dari hasil eksekusi aktual.

Kedua format memakai data yang sama dengan builder PDF dan Visualizer;
tidak ada nilai yang dihasilkan ulang atau di-hardcode di sini.
"""

from __future__ import annotations

import csv
from io import StringIO

from crypto.encoding import display_text, format_bin, format_hex, int16_to_hex
from crypto.pipeline import normalize_mode
from crypto.results import ModeResult

__all__ = ["results_to_markdown", "results_to_csv"]


def _as_result_map(results) -> dict[str, ModeResult]:
    """Terima None, satu ModeResult, list, atau dict; kembalikan dict per mode."""
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


def _status_text(result: ModeResult | None) -> str:
    if result is None:
        return "Belum dijalankan"
    return "BERHASIL" if result.verified else "GAGAL"


def results_to_markdown(results) -> str:
    """Susun laporan Markdown dari data eksekusi aktual."""
    result_map = _as_result_map(results)
    lines: list[str] = [
        "# Laporan CipherLab",
        "",
        "Semua nilai berasal dari eksekusi aktual aplikasi (bukan data contoh).",
        "",
        "## Ringkasan",
        "",
        "| Mode | Status Eksekusi | Verifikasi | Blok | Ciphertext (byte) |",
        "|---|---|---|---|---|",
    ]
    for mode in ("ECB", "CBC", "CTR"):
        result = result_map.get(mode)
        if result is None:
            lines.append(f"| {mode} | Belum dijalankan | - | - | - |")
        else:
            lines.append(
                f"| {mode} | Dijalankan | {_status_text(result)} | "
                f"{result.block_count} | {result.ciphertext_length} |"
            )

    for mode in ("ECB", "CBC", "CTR"):
        result = result_map.get(mode)
        lines += ["", f"## Mode {mode}", ""]
        if result is None:
            lines.append(
                f"**Belum dijalankan.** Mode {mode} belum dieksekusi pada sesi ini; "
                "tidak ada data yang dapat dilaporkan."
            )
            continue
        lines += [
            f"- Waktu eksekusi: {result.executed_at.strftime('%d/%m/%Y %H:%M:%S %Z')}",
            f"- Plaintext: `{display_text(result.plaintext_text, limit=500)}` "
            f"({len(result.plaintext_bytes)} byte, {result.encoding})",
            f"- Kunci: `0x{int16_to_hex(result.key)}`",
        ]
        if mode == "CBC":
            lines.append(f"- IV: `0x{int16_to_hex(result.iv)}`")
        if mode == "CTR":
            lines.append(
                f"- Counter awal: `0x{int16_to_hex(result.initial_counter)}` "
                "(increment +1 per blok)"
            )
        lines += [
            f"- Padding: {result.padding or 'tidak digunakan (panjang dipertahankan)'}",
            f"- Hasil dekripsi: `{display_text(result.decrypted_text, limit=500)}`",
            f"- Status verifikasi: **{_status_text(result)}**",
            "",
            "| Blok | Plaintext HEX | Plaintext BIN | Ciphertext HEX | Ciphertext BIN |",
            "|---|---|---|---|---|",
        ]
        for block in result.blocks:
            lines.append(
                f"| {block.number} | `{format_hex(block.plaintext_block)}` | "
                f"`{format_bin(block.plaintext_block)}` | "
                f"`{format_hex(block.ciphertext_block)}` | "
                f"`{format_bin(block.ciphertext_block)}` |"
            )

    return "\n".join(lines) + "\n"


_CSV_HEADER = [
    "mode",
    "blok",
    "plaintext_hex",
    "plaintext_bin",
    "ciphertext_hex",
    "ciphertext_bin",
    "xor_value_hex",
    "counter_hex",
    "keystream_hex",
    "jumlah_blok",
    "ciphertext_byte",
    "verifikasi",
]


def results_to_csv(results) -> str:
    """Susun CSV per blok dari data eksekusi aktual (satu baris per blok)."""
    result_map = _as_result_map(results)
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(_CSV_HEADER)

    for mode in ("ECB", "CBC", "CTR"):
        result = result_map.get(mode)
        if result is None:
            writer.writerow([mode, "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "Belum dijalankan"])
            continue
        for block in result.blocks:
            writer.writerow(
                [
                    mode,
                    block.number,
                    format_hex(block.plaintext_block),
                    format_bin(block.plaintext_block),
                    format_hex(block.ciphertext_block),
                    format_bin(block.ciphertext_block),
                    format_hex(block.xor_value) if block.xor_value else "",
                    format_hex(block.counter_block) if block.counter_block else "",
                    format_hex(block.keystream) if block.keystream else "",
                    result.block_count,
                    result.ciphertext_length,
                    _status_text(result),
                ]
            )
    return buffer.getvalue()
