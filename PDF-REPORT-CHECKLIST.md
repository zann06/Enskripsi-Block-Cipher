# PDF Report Feature — Implementation Checklist

- [ ] Tambahkan `reportlab` ke `requirements.txt`.
- [ ] Buat struktur data hasil eksekusi yang konsisten untuk ECB/CBC/CTR.
- [ ] Simpan hasil aktual setiap eksekusi di `st.session_state`.
- [ ] Tambahkan metadata laporan yang dapat diedit.
- [ ] Buat daftar anggota dinamis.
- [ ] Buat nama file otomatis dari nama kelompok/judul, tetapi tetap editable.
- [ ] Sanitasi nama file.
- [ ] Implementasikan PDF dengan ReportLab: cover, identitas, ringkasan, hasil per mode, tabel blok, trace, verifikasi, perbandingan, kesimpulan, batasan keamanan, footer dan nomor halaman.
- [ ] Tandai mode yang belum dijalankan tanpa mengarang hasil.
- [ ] Buat `st.download_button` yang mengirim bytes PDF aktual.
- [ ] Uji PDF kosong/parsial, semua mode, verifikasi gagal, anggota banyak, nama file aneh, dan tabel panjang.
- [ ] Pastikan data PDF cocok dengan hasil UI.
- [ ] Dokumentasikan fitur pada README.
