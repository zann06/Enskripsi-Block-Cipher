"""Test ekspor Markdown dan CSV dari hasil eksekusi aktual."""

import csv
import io

from crypto.pipeline import execute_mode
from reports.export import results_to_csv, results_to_markdown

KEY = 0x1A2B
PLAINTEXT = "Halo dunia! Ekspor laporan."


def _results_all():
    return {
        "ECB": execute_mode("ECB", PLAINTEXT, KEY),
        "CBC": execute_mode("CBC", PLAINTEXT, KEY, iv=0x0F0F),
        "CTR": execute_mode("CTR", PLAINTEXT, KEY, initial_counter=0x00C8),
    }


def test_markdown_contains_actual_data():
    results = _results_all()
    md = results_to_markdown(results)
    for result in results.values():
        assert f"## Mode {result.mode}" in md
        assert f"**Status verifikasi: {result.status}**" in md
        for block in result.blocks:
            assert f"`{block.ciphertext_block.hex(' ').upper()}`" in md
    assert "0x0F0F" in md and "0x00C8" in md and "0x1A2B" in md
    assert "Belum dijalankan" not in md


def test_markdown_marks_missing_modes():
    results = {"ECB": execute_mode("ECB", PLAINTEXT, KEY)}
    md = results_to_markdown(results)
    assert "Belum dijalankan" in md
    assert "**Belum dijalankan.** Mode CBC" in md
    assert results["ECB"].blocks[0].ciphertext_block.hex(" ").upper() in md


def test_markdown_empty_session():
    md = results_to_markdown(None)
    assert md.count("Belum dijalankan") >= 3
    assert "tidak ada data" in md


def test_csv_rows_match_execution_objects():
    results = _results_all()
    csv_text = results_to_csv(results)
    rows = list(csv.reader(io.StringIO(csv_text)))
    header = rows[0]
    assert header[:6] == ["mode", "blok", "plaintext_hex", "plaintext_bin",
                          "ciphertext_hex", "ciphertext_bin"]
    data_rows = rows[1:]
    expected_blocks = sum(r.block_count for r in results.values())
    assert len(data_rows) == expected_blocks

    by_mode = {row[0]: [] for row in data_rows}
    for row in data_rows:
        by_mode[row[0]].append(row)
    for mode, result in results.items():
        for row, block in zip(by_mode[mode], result.blocks):
            assert int(row[1]) == block.number
            assert row[2] == block.plaintext_block.hex(" ").upper()
            assert row[4] == block.ciphertext_block.hex(" ").upper()
            assert row[-1] == result.status


def test_csv_marks_missing_modes():
    csv_text = results_to_csv({"ECB": execute_mode("ECB", "AB", KEY)})
    rows = list(csv.reader(io.StringIO(csv_text)))
    missing = [row for row in rows[1:] if row[-1] == "Belum dijalankan"]
    assert [row[0] for row in missing] == ["CBC", "CTR"]


def test_csv_empty_session():
    rows = list(csv.reader(io.StringIO(results_to_csv(None))))
    assert len(rows) == 4  # header + 3 placeholder
