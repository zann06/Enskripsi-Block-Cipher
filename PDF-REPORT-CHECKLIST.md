# PDF Report Feature — Implementation Checklist

Status: **selesai** (seluruh item terverifikasi oleh `tests/test_pdf_report.py`, 171 test pytest lulus).

- [x] Tambahkan `reportlab` ke `requirements.txt` (+ `pypdf` untuk pengujian isi PDF).
- [x] Buat struktur data hasil eksekusi yang konsisten untuk ECB/CBC/CTR (`crypto/results.py`).
- [x] Simpan hasil aktual setiap eksekusi di `st.session_state`.
- [x] Tambahkan metadata laporan yang dapat diedit (`ReportMetadata`).
- [x] Buat daftar anggota dinamis (nama wajib, NIM opsional, tambah/hapus).
- [x] Buat nama file otomatis dari nama kelompok/judul, tetap editable.
- [x] Sanitasi nama file (karakter tidak aman, nama cadangan Windows, batas panjang).
- [x] Implementasikan PDF dengan ReportLab: cover, identitas, daftar isi, ringkasan, hasil per mode, ciphertext lengkap, tabel blok HEX/BIN, trace ronde, verifikasi, perbandingan, kesimpulan, batasan keamanan, header/footer, nomor halaman, lampiran trace & jadwal kunci.
- [x] Tandai mode yang belum dijalankan tanpa mengarang hasil ("Belum dijalankan").
- [x] Buat `st.download_button` yang mengirim bytes PDF aktual.
- [x] Uji PDF kosong/parsial, semua mode, verifikasi gagal, anggota banyak, nama file aneh, dan tabel panjang lintas halaman.
- [x] Pastikan data PDF cocok dengan hasil UI (ekstraksi teks PDF dibandingkan dengan objek `ModeResult`).
- [x] Dokumentasikan fitur pada README (cara mengisi identitas dan mengunduh laporan).
- [x] Periksa visual: render seluruh halaman contoh PDF (cover, daftar isi, tabel lintas halaman, karakter Unicode) dan bersihkan data pribadi dari contoh yang dipublikasikan.
