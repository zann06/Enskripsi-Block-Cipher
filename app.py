"""CipherLab - aplikasi Streamlit untuk block cipher 16-bit (ECB, CBC, CTR).

Semua hasil yang ditampilkan berasal dari eksekusi aktual modul ``crypto``.
Hasil setiap eksekusi disimpan di ``st.session_state["results"]`` dan dipakai
bersama oleh halaman Visualizer dan Reports (termasuk builder PDF).
"""

from __future__ import annotations

import uuid
from datetime import date

import streamlit as st

from crypto.encoding import (
    display_text,
    format_bin,
    format_hex,
    int16_to_bin,
    int16_to_hex,
    parse_counter,
    parse_iv,
    parse_key,
)
from crypto.feistel16 import (
    BLOCK_BITS,
    BLOCK_BYTES,
    CipherValueError,
    ROUNDS,
    format_round_traces,
    key_schedule,
)
from crypto.pipeline import SUPPORTED_MODES, execute_mode, redecrypt_result
from crypto.results import ModeResult
from reports import ReportLabMissingError, ReportMetadata, Member, build_pdf_bytes, default_filename, resolve_filename
from reports.export import results_to_csv, results_to_markdown

st.set_page_config(
    page_title="CipherLab",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)


def go_to(page: str) -> None:
    """Target navigasi diterapkan sebelum widget radio dibuat ulang pada rerun."""
    st.session_state["nav_target"] = page
    st.rerun()

MONTHS_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def format_date_id(value: date) -> str:
    return f"{value.day} {MONTHS_ID[value.month - 1]} {value.year}"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

DEFAULT_TITLE = "Laporan Praktikum Block Cipher 16-bit"
EXAMPLE_PLAINTEXT = "Kriptografi itu menyenangkan!"
EXAMPLE_KEY = "1A2B"
EXAMPLE_IV = "0F0F"
EXAMPLE_COUNTER = "00C8"


def init_state() -> None:
    defaults = {
        "results": {},
        "last_mode": None,
        "members": [],
        "pdf_filename_edited": False,
        "include_traces": True,
        "id_title": DEFAULT_TITLE,
        "id_group": "",
        "id_course": "",
        "id_lecturer": "",
        "id_class": "",
        "id_notes": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _auto_filename() -> None:
    """Perbarui nama file otomatis selama pengguna belum mengeditnya sendiri."""
    if not st.session_state.get("pdf_filename_edited"):
        st.session_state["pdf_filename"] = default_filename(
            st.session_state.get("id_group", ""), st.session_state.get("id_title", "")
        )


def _mark_filename_edited() -> None:
    st.session_state["pdf_filename_edited"] = True


def get_members() -> list[Member]:
    """Baca baris anggota dari widget menjadi daftar Member tervalidasi ringan."""
    members: list[Member] = []
    for row in st.session_state.get("members", []):
        uid = row["uid"]
        name = str(st.session_state.get(f"m_name_{uid}", "")).strip()
        nim = str(st.session_state.get(f"m_nim_{uid}", "")).strip()
        members.append(Member(name=name, nim=nim))
    return members


def build_metadata() -> ReportMetadata:
    date_value = st.session_state.get("id_date", date.today())
    return ReportMetadata(
        title=st.session_state.get("id_title", ""),
        group_name=st.session_state.get("id_group", ""),
        course=st.session_state.get("id_course", ""),
        lecturer=st.session_state.get("id_lecturer", ""),
        class_name=st.session_state.get("id_class", ""),
        members=get_members(),
        report_date=format_date_id(date_value) if isinstance(date_value, date) else str(date_value),
        notes=st.session_state.get("id_notes", ""),
        filename=st.session_state.get("pdf_filename", ""),
    )


# ---------------------------------------------------------------------------
# Halaman
# ---------------------------------------------------------------------------


def page_dashboard() -> None:
    st.markdown("## Belajar block cipher secara visual")
    st.write(
        "CipherLab adalah playground edukasi untuk enkripsi dan dekripsi block cipher "
        f"berukuran {BLOCK_BITS} bit ({BLOCK_BYTES} byte). Jalankan mode ECB, CBC, atau CTR, "
        "telusuri perhitungan per blok, verifikasi dekripsi, lalu unduh laporan PDF "
        "dari hasil eksekusi aktual."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Cipher inti", "Feistel 16-bit", f"{ROUNDS} ronde (toy, edukasional)")
    col2.metric("Ukuran blok", f"{BLOCK_BITS} bit", f"{BLOCK_BYTES} byte per blok")
    col3.metric("Mode", "3 mode", "ECB, CBC, CTR")

    st.warning(
        "Peringatan: toy Feistel 16-bit hanya untuk pembelajaran. Bukan AES dan tidak aman "
        "untuk melindungi data nyata."
    )

    left, middle, right = st.columns(3)
    if left.button("Buka Playground", type="primary", use_container_width=True):
        go_to("Playground")
    if middle.button("Buka Visualizer", use_container_width=True):
        go_to("Visualizer")
    if right.button("Buat Laporan PDF", use_container_width=True):
        go_to("Reports")

    st.subheader("Status eksekusi saat ini")
    results: dict[str, ModeResult] = st.session_state["results"]
    if not results:
        st.info("Belum ada mode yang dijalankan pada sesi ini. Mulai dari Playground.")
    else:
        chips = []
        for mode in SUPPORTED_MODES:
            result = results.get(mode)
            if result is None:
                chips.append(f"{mode}: belum dijalankan")
            elif result.verified:
                chips.append(f"{mode}: BERHASIL diverifikasi")
            else:
                chips.append(f"{mode}: verifikasi GAGAL")
        st.write(" - ".join(chips))


def _parse_inputs(mode: str) -> tuple[int, int | None, int | None]:
    """Parse input form; melempar CipherValueError dengan pesan ramah."""
    key = parse_key(st.session_state.get("pg_key", ""))
    iv = parse_iv(st.session_state.get("pg_iv", "")) if mode == "CBC" else None
    counter = parse_counter(st.session_state.get("pg_counter", "")) if mode == "CTR" else None
    return key, iv, counter


def _show_mode_result(result: ModeResult) -> None:
    st.subheader(f"Hasil {result.mode}")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Jumlah blok", result.block_count)
    col_b.metric("Panjang ciphertext", f"{result.ciphertext_length} byte")
    col_c.metric("Padding", "PKCS#7 2B" if result.padding else "Tanpa padding")

    st.markdown(f"**Ciphertext HEX**\n```\n{format_hex(result.ciphertext)}\n```")
    st.markdown(f"**Ciphertext BIN**\n```\n{format_bin(result.ciphertext)}\n```")

    if result.decryption_error:
        st.error(f"Dekripsi menghasilkan error: {result.decryption_error}")
    else:
        st.markdown(f"**Plaintext hasil dekripsi:** {display_text(result.decrypted_text) or '(kosong)'}")

    if result.verified:
        st.success("Verifikasi round-trip: BERHASIL - hasil dekripsi identik dengan plaintext asli.")
    else:
        st.error("Verifikasi round-trip: GAGAL - hasil dekripsi TIDAK sama dengan plaintext asli.")

    rows = []
    for block in result.blocks:
        row = {
            "Blok": block.number,
            "Plaintext HEX": format_hex(block.plaintext_block),
            "Ciphertext HEX": format_hex(block.ciphertext_block),
            "Ciphertext BIN": format_bin(block.ciphertext_block),
        }
        if result.mode == "CBC":
            row["XOR dgn (IV/C prev)"] = format_hex(block.xor_value or b"")
            row["Input Feistel"] = format_hex(block.feistel_input)
        if result.mode == "CTR":
            row["Counter"] = format_hex(block.counter_block or b"")
            row["Keystream"] = format_hex(block.keystream or b"")
        rows.append(row)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)


def page_playground() -> None:
    st.header("Playground")
    st.write("Masukkan plaintext dan kunci, pilih mode, lalu jalankan Encrypt dan Decrypt.")

    st.text_area("Plaintext", key="pg_plaintext", height=110,
                 help="Teks apa pun; dikonversi ke UTF-8.")
    st.text_input("Kunci (HEX 16-bit, contoh: 1A2B)", key="pg_key")

    mode = st.selectbox("Mode", SUPPORTED_MODES, key="pg_mode")
    if mode == "CBC":
        st.text_input("IV (HEX 16-bit, contoh: 0F0F)", key="pg_iv")
    if mode == "CTR":
        st.text_input("Counter awal (HEX 16-bit, contoh: 00C8)", key="pg_counter",
                      help="Counter bertambah +1 per blok dan tidak boleh melewati 0xFFFF.")

    col_enc, col_dec, col_ex, col_clear = st.columns([1.2, 1.2, 1.2, 0.8])
    do_encrypt = col_enc.button("Encrypt", type="primary", use_container_width=True)
    do_decrypt = col_dec.button("Decrypt", use_container_width=True)
    do_example = col_ex.button("Use Example", use_container_width=True)
    do_clear = col_clear.button("Clear", use_container_width=True)

    if do_example:
        st.session_state["pg_plaintext"] = EXAMPLE_PLAINTEXT
        st.session_state["pg_key"] = EXAMPLE_KEY
        st.session_state["pg_iv"] = EXAMPLE_IV
        st.session_state["pg_counter"] = EXAMPLE_COUNTER
        st.rerun()

    if do_clear:
        for key in ("pg_plaintext", "pg_key", "pg_iv", "pg_counter"):
            st.session_state.pop(key, None)
        st.rerun()

    results: dict[str, ModeResult] = st.session_state["results"]

    if do_encrypt:
        plaintext = st.session_state.get("pg_plaintext", "")
        try:
            key, iv, counter = _parse_inputs(mode)
            result = execute_mode(mode, plaintext, key, iv=iv, initial_counter=counter,
                                  collect_trace=True)
            results[result.mode] = result
            st.session_state["last_mode"] = result.mode
            st.success(f"Enkripsi {result.mode} selesai: {result.block_count} blok.")
            _show_mode_result(result)
        except (CipherValueError, ValueError) as exc:
            st.error(str(exc))

    if do_decrypt:
        result = results.get(mode)
        if result is None:
            st.warning(f"Belum ada hasil {mode} yang disimpan. Jalankan Encrypt terlebih dahulu.")
        else:
            try:
                key, iv, counter = _parse_inputs(mode)
                updated = redecrypt_result(result, key=key, iv=iv, initial_counter=counter)
                results[updated.mode] = updated
                st.session_state["last_mode"] = updated.mode
                if updated.verified:
                    st.success("Decrypt selesai dan verifikasi BERHASIL.")
                else:
                    st.error("Decrypt selesai namun verifikasi GAGAL (periksa kunci/IV/counter).")
                _show_mode_result(updated)
            except (CipherValueError, ValueError) as exc:
                st.error(f"Parameter tidak valid: {exc}")

    if not do_encrypt and not do_decrypt:
        last = st.session_state.get("last_mode")
        if last and last in results:
            st.caption(f"Hasil terakhir: mode {last}.")
            _show_mode_result(results[last])
        else:
            st.info("Belum ada eksekusi pada sesi ini. Gunakan Use Example untuk mengisi form contoh.")


def page_visualizer() -> None:
    st.header("Visualizer")
    results: dict[str, ModeResult] = st.session_state["results"]
    executed = [mode for mode in SUPPORTED_MODES if mode in results]
    if not executed:
        st.info("Belum ada mode yang dijalankan. Jalankan Encrypt pada Playground terlebih dahulu.")
        return

    default_index = executed.index(st.session_state["last_mode"]) if st.session_state.get("last_mode") in executed else 0
    mode = st.selectbox("Pilih mode yang sudah dijalankan", executed, index=default_index)
    result = results[mode]

    st.caption(
        f"Dijalankan {result.executed_at.strftime('%d/%m/%Y %H:%M:%S')} - "
        f"kunci 0x{int16_to_hex(result.key)} - "
        + (f"IV 0x{int16_to_hex(result.iv)}" if mode == "CBC" else
           f"counter awal 0x{int16_to_hex(result.initial_counter)}" if mode == "CTR" else "tanpa IV")
        + f" - status verifikasi {'BERHASIL' if result.verified else 'GAGAL'}"
    )

    rows = []
    for block in result.blocks:
        row = {
            "Blok": block.number,
            "Plaintext HEX": format_hex(block.plaintext_block),
            "Plaintext BIN": format_bin(block.plaintext_block),
            "Ciphertext HEX": format_hex(block.ciphertext_block),
            "Ciphertext BIN": format_bin(block.ciphertext_block),
        }
        if mode == "CBC":
            row["XOR dgn (IV/C prev)"] = format_hex(block.xor_value or b"")
            row["Input Feistel"] = format_hex(block.feistel_input)
        if mode == "CTR":
            row["Counter"] = format_hex(block.counter_block or b"")
            row["Keystream"] = format_hex(block.keystream or b"")
        rows.append(row)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Plaintext kosong: tidak ada blok yang diproses pada mode ini (CTR tanpa padding).")

    if result.blocks:
        valid_numbers = [block.number for block in result.blocks]
        if st.session_state.get("viz_block") not in valid_numbers:
            st.session_state.pop("viz_block", None)
        block_number = st.selectbox(
            "Pilih blok untuk melihat trace ronde Feistel",
            valid_numbers,
            key="viz_block",
        )
        block = result.blocks[block_number - 1]
        st.subheader(f"Trace ronde Feistel - {mode} blok {block_number} (enkripsi)")
        st.dataframe(format_round_traces(block.feistel_rounds), use_container_width=True, hide_index=True)

    st.subheader("Jadwal kunci (key schedule)")
    round_keys = key_schedule(result.key)
    st.caption(", ".join(f"k{i + 1}=0x{rk:02X}" for i, rk in enumerate(round_keys)))


def page_comparison() -> None:
    st.header("Comparison")
    st.write("Perbandingan karakteristik mode dan pengamatan dari eksekusi aktual pada sesi ini.")

    st.markdown(
        """
        | Aspek | ECB | CBC | CTR |
        |---|---|---|---|
        | Rumus enkripsi | `C_i = E_K(P_i)` | `C_i = E_K(P_i XOR C_i-1)` | `C_i = P_i XOR E_K(T_i)` |
        | Rumus dekripsi | `P_i = D_K(C_i)` | `P_i = D_K(C_i) XOR C_i-1` | `P_i = C_i XOR E_K(T_i)` |
        | IV / counter | Tidak digunakan | IV 16-bit (`C_0 = IV`) | Counter awal 16-bit, +1 per blok |
        | Padding | PKCS#7 2 byte | PKCS#7 2 byte | Tanpa padding |
        | Dependensi antarblok | Independen | Bergantung blok sebelumnya | Melalui counter/keystream |
        | Pola blok berulang | Terlihat pada ciphertext | Tersamarkan oleh chaining | Keystream berbeda per blok |
        """
    )
    st.caption(
        "Catatan: mode dasar tanpa autentikasi (MAC/AEAD) tidak menjamin integritas ciphertext. "
        "Tabel di atas adalah spesifikasi mode, bukan hasil eksekusi."
    )

    st.subheader("Pengamatan dari eksekusi aktual")
    results: dict[str, ModeResult] = st.session_state["results"]
    rows = []
    for mode in SUPPORTED_MODES:
        result = results.get(mode)
        if result is None:
            rows.append({"Mode": mode, "Status": "Belum dijalankan", "Verifikasi": "-",
                         "Blok": "-", "Ciphertext (byte)": "-", "Blok plaintext berulang": "-"})
            continue
        plain_counts: dict[bytes, int] = {}
        for block in result.blocks:
            plain_counts[block.plaintext_block] = plain_counts.get(block.plaintext_block, 0) + 1
        repeated = sum(count - 1 for count in plain_counts.values() if count > 1)
        cipher_identical = "n/a"
        if repeated:
            identical = all(
                len({b.ciphertext_block for b in result.blocks if b.plaintext_block == value}) == 1
                for value, count in plain_counts.items() if count > 1
            )
            cipher_identical = "identik" if identical else "berbeda"
        rows.append({
            "Mode": mode,
            "Status": "Dijalankan",
            "Verifikasi": "BERHASIL" if result.verified else "GAGAL",
            "Blok": result.block_count,
            "Ciphertext (byte)": result.ciphertext_length,
            "Blok plaintext berulang": f"{repeated} (ciphertext {cipher_identical})" if repeated else "tidak ada",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_member_rows() -> None:
    """Baris anggota dinamis; tiap baris punya uid stabil agar widget tidak tertukar."""
    st.write("Anggota kelompok (nama wajib, NIM opsional):")
    to_delete: list[str] = []
    members = st.session_state.get("members", [])
    if not members:
        st.caption("Belum ada baris anggota. Tambahkan minimal satu anggota.")
    for row in members:
        uid = row["uid"]
        col_name, col_nim, col_del = st.columns([3, 2, 0.5])
        col_name.text_input("Nama", key=f"m_name_{uid}", placeholder="Nama anggota",
                            label_visibility="collapsed")
        col_nim.text_input("NIM", key=f"m_nim_{uid}", placeholder="NIM (opsional)",
                           label_visibility="collapsed")
        if col_del.button("Hapus", key=f"m_del_{uid}", use_container_width=True):
            to_delete.append(uid)
    if to_delete:
        st.session_state["members"] = [r for r in members if r["uid"] not in to_delete]
        st.rerun()
    if st.button("Tambah anggota", key="add_member"):
        st.session_state["members"] = members + [{"uid": uuid.uuid4().hex, "name": "", "nim": ""}]
        st.rerun()


def page_reports() -> None:
    st.header("Reports - Laporan PDF")
    st.write(
        "Isi identitas kelompok, jalankan ECB/CBC/CTR di Playground, lalu unduh laporan PDF "
        "yang dibangun dari hasil eksekusi aktual pada sesi ini."
    )

    left_col, right_col = st.columns([1.15, 1])

    with left_col:
        st.subheader("Identitas Laporan")
        st.text_input("Judul laporan (wajib)", key="id_title", on_change=_auto_filename)
        st.text_input("Nama kelompok (wajib)", key="id_group", on_change=_auto_filename)
        col_a, col_b = st.columns(2)
        col_a.text_input("Mata kuliah", key="id_course")
        col_b.text_input("Dosen", key="id_lecturer")
        st.text_input("Kelas / kelas praktikum", key="id_class")
        st.date_input("Tanggal laporan", key="id_date")
        st.text_area("Catatan tambahan (opsional)", key="id_notes", height=80)

        _render_member_rows()

        st.subheader("Nama file PDF")
        st.text_input(
            "Nama file (tanpa .pdf)",
            key="pdf_filename",
            on_change=_mark_filename_edited,
            help="Terisi otomatis dari nama kelompok/judul dan dapat diedit bebas.",
        )
        if st.button("Kembalikan ke nama otomatis", key="reset_filename"):
            st.session_state["pdf_filename_edited"] = False
            _auto_filename()
            st.rerun()

    with right_col:
        st.subheader("Status pengujian")
        results: dict[str, ModeResult] = st.session_state["results"]
        checklist = []
        for mode in SUPPORTED_MODES:
            result = results.get(mode)
            if result is None:
                checklist.append(f"- {mode}: **belum dijalankan**")
            elif result.verified:
                checklist.append(f"- {mode}: dijalankan, verifikasi **BERHASIL**")
            else:
                checklist.append(f"- {mode}: dijalankan, verifikasi **GAGAL**")
        st.markdown("\n".join(checklist))
        executed = [m for m in SUPPORTED_MODES if m in results]
        verified = [m for m in executed if results[m].verified]
        if not executed:
            st.warning("Tombol unduh aktif setelah minimal satu eksekusi tersedia. Jalankan mode pada Playground.")
        elif len(verified) < 3:
            st.info(
                "Untuk laporan tugas yang lengkap, jalankan dan verifikasi ketiga mode "
                "(saat ini " + f"{len(verified)}/3 BERHASIL)."
            )
        else:
            st.success("Ketiga mode dijalankan dan lolos verifikasi.")

        st.checkbox("Sertakan Lampiran trace ronde lengkap (per blok)", key="include_traces")

        metadata = build_metadata()
        can_download = bool(executed)
        pdf_bytes = None
        if can_download:
            try:
                pdf_bytes = build_pdf_bytes(metadata, results, include_traces=st.session_state["include_traces"])
            except ReportLabMissingError as exc:
                st.error(str(exc))
                can_download = False
            except ValueError as exc:
                st.error(str(exc))
                can_download = False

        st.download_button(
            "Unduh Laporan PDF",
            data=pdf_bytes if pdf_bytes else b"",
            file_name=f"{resolve_filename(metadata)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            disabled=not can_download,
            key="download_pdf",
        )
        st.caption(
            "PDF dibuat lokal dengan ReportLab dari data eksekusi aktual. "
            "Mode yang belum dijalankan ditandai 'Belum dijalankan' di PDF."
        )

        st.divider()
        st.subheader("Ekspor Markdown / CSV")
        md_data = results_to_markdown(results)
        csv_data = results_to_csv(results)
        st.download_button("Unduh Markdown", data=md_data, file_name="laporan_cipherlab.md",
                           mime="text/markdown", use_container_width=True, disabled=not executed)
        st.download_button("Unduh CSV", data=csv_data, file_name="hasil_cipherlab.csv",
                           mime="text/csv", use_container_width=True, disabled=not executed)


PAGES = {
    "Dashboard": page_dashboard,
    "Playground": page_playground,
    "Visualizer": page_visualizer,
    "Comparison": page_comparison,
    "Reports": page_reports,
}


def main() -> None:
    init_state()

    target = st.session_state.pop("nav_target", None)
    if target and target in PAGES:
        st.session_state["nav"] = target

    with st.sidebar:
        st.markdown("### CipherLab")
        st.caption("Educational project - 16-bit blocks")
        st.radio("Navigasi", list(PAGES), key="nav")
        st.divider()
        executed = [m for m in SUPPORTED_MODES if m in st.session_state["results"]]
        st.caption(
            f"Mode dijalankan: {', '.join(executed) if executed else 'belum ada'}"
        )
        st.caption("Toy Feistel 16-bit - hanya untuk edukasi.")

    PAGES[st.session_state["nav"]]()


if __name__ == "__main__":
    main()
