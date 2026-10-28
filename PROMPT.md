# PROMPT.md — Master Prompt untuk OpenCode

## Peran
Bertindak sebagai Senior Python Developer, Cryptography Engineer, UI/UX Designer, dan QA Engineer. Bangun **CipherLab**, aplikasi web edukasi untuk enkripsi/dekripsi block cipher 16-bit dengan mode ECB, CBC, dan CTR.

Jangan hanya membuat mockup. Semua hasil ciphertext, trace, dan laporan harus berasal dari perhitungan aktual yang diuji.

## Sebelum mulai
1. Periksa repository, file yang tersedia, dan `PRD.md`.
2. Jika `docs/design-reference.png` tersedia, gunakan sebagai referensi visual, bukan sebagai gambar UI yang ditempel mentah.
3. Jika dosen ternyata menentukan algoritma cipher tertentu, jangan mengasumsikan Feistel; minta klarifikasi atau ikuti spesifikasi tersebut.
4. Buat rencana singkat lalu lanjutkan implementasi tanpa menunggu persetujuan untuk keputusan teknis yang sudah ditentukan PRD.

## Stack
- Python 3.11+
- Streamlit
- Pytest atau unittest
- Pandas hanya bila dibutuhkan
- Tidak ada backend, database, atau API AI runtime.

## Algoritma
Jika tidak ada algoritma spesifik dari dosen, implementasikan toy Feistel 16-bit, 8 ronde, key schedule deterministik, dokumentasi fungsi ronde, dan fungsi encrypt/decrypt yang saling invers. Tegaskan bahwa ini hanya algoritma edukasional dan bukan cipher aman untuk penggunaan nyata. Jangan menyebutnya AES.

Ukuran blok 16 bit = 2 byte. Implementasikan:
- ECB: `C_i = E_K(P_i)`
- CBC: `C_i = E_K(P_i XOR C_(i-1))`, `C_0 = IV`
- CTR: `C_i = P_i XOR E_K(T_i)`, counter block bertambah dengan aturan yang terdokumentasi.

Persyaratan:
- Teks UTF-8.
- Tampilkan HEX dan biner.
- ECB/CBC menggunakan PKCS#7 yang disesuaikan dengan blok 2 byte.
- CTR tanpa padding dan mempertahankan panjang byte.
- Validasi key 16-bit, IV CBC 16-bit, initial counter CTR 16-bit, serta overflow counter.
- CBC decrypt harus menggunakan inverse cipher dan XOR terhadap IV/ciphertext sebelumnya.
- CTR decrypt menggunakan keystream yang sama.
- Jangan menggunakan XOR dengan key sebagai satu-satunya cipher.
- Jangan membuat ciphertext atau trace palsu.

## Fitur UI
Buat UI Streamlit modern, minimalis, dark navy dengan aksen violet/cyan:
- Background `#0B1020`
- Surface `#151C30`
- Violet `#8B5CF6`
- Cyan `#22D3EE`
- Text `#F3F4F6`
- Muted `#94A3B8`

Gunakan sidebar navigasi sederhana untuk:
1. Dashboard
2. Playground
3. Visualizer
4. Comparison
5. Reports

Playground:
- Input plaintext, key, mode, IV/counter yang hanya muncul sesuai mode.
- Tombol Encrypt, Decrypt, Clear, Use Example.
- Ciphertext HEX dan BIN.
- Hasil dekripsi dan status verifikasi.
- Error handling yang ramah pengguna.

Visualizer:
- Pecah data ke blok 16-bit.
- Tampilkan tabel plaintext/ciphertext per blok dalam HEX dan BIN.
- Tampilkan XOR, IV/chaining CBC, counter dan keystream CTR.
- Tampilkan trace ronde Feistel untuk blok yang dipilih bila implementasinya mendukung.
- Semua nilai berasal dari eksekusi aktual.

Comparison:
- Bandingkan pola ECB, chaining CBC, dan keystream CTR.
- Jelaskan IV/counter, padding, dependensi antarblok, serta batas keamanan.
- Jangan membuat klaim keamanan absolut.

Reports:
- Parameter eksekusi, tabel blok, ciphertext, hasil dekripsi, status verifikasi.
- Ekspor Markdown dan CSV.
- Isi laporan harus berasal dari data aktual.

## Testing wajib
Tulis dan jalankan test untuk:
1. `decrypt_block(encrypt_block(x, key), key) == x`.
2. Seluruh 65.536 nilai blok 16-bit pada kunci uji yang valid jika performanya memungkinkan; jika tidak, jelaskan batas pengujian dan tambahkan pengujian exhaustive terpisah.
3. Round-trip ECB, CBC, CTR.
4. Plaintext kosong, panjang ganjil, beberapa blok, dan UTF-8 non-ASCII.
5. Padding valid/invalid.
6. Key/IV/counter invalid.
7. Counter overflow.
8. Output laporan sesuai data eksekusi.

Jangan membuat expected output dengan memanggil fungsi yang sedang diuji. Buat setidaknya satu known-answer test yang independen dan terdokumentasi.

## Alur kerja
1. Implementasikan cipher inti dan unit test terlebih dahulu.
2. Implementasikan mode operasi.
3. Jalankan test.
4. Bangun UI dan hubungkan ke algoritma aktual.
5. Tambahkan visualisasi dan ekspor laporan.
6. Jalankan semua test, compile/check bila tersedia, dan `streamlit run app.py` atau smoke test yang sesuai.
7. Perbaiki error yang ditemukan.
8. Lengkapi README dan contoh eksekusi.

## Struktur
Gunakan modul terpisah dalam `crypto/`: `feistel16.py`, `ecb.py`, `cbc.py`, `ctr.py`, `padding.py`, dan `encoding.py`. Simpan test di `tests/`.

## Kriteria selesai
- Tiga mode bekerja.
- Enkripsi/dekripsi benar dan round-trip lolos.
- Visualizer memakai data aktual.
- Laporan dapat diunduh.
- UI minimalis dan usable.
- Semua test yang diklaim lulus benar-benar dijalankan.
- README memberi instruksi setup yang bisa diikuti.
- Catat file yang dibuat, perintah test, hasil aktual, cara menjalankan, dan keterbatasan yang tersisa.

Mulai dengan memeriksa repository lalu implementasikan proyek secara bertahap. Jangan berhenti setelah menulis rencana.


## 11. FITUR TAMBAHAN WAJIB — BUILDER LAPORAN PDF

Implementasikan fitur PDF end-to-end di aplikasi. Jangan hanya membuat template statis atau tautan ke PDF contoh.

### UI Identitas Laporan
Tambahkan panel atau tab “Identitas Laporan” dengan:
- Judul laporan (wajib).
- Nama kelompok (wajib).
- Mata kuliah.
- Nama dosen.
- Kelas.
- Daftar anggota yang dapat ditambah/dihapus; nama wajib, NIM opsional.
- Tanggal laporan, default tanggal hari ini dan dapat diedit.
- Catatan tambahan opsional.
- Nama file PDF yang dibuat otomatis dari nama kelompok/judul dan dapat diedit.

Jangan hardcode nama kelompok atau anggota. Gunakan state Streamlit dan validasi input. Sanitasi nama file menjadi nama yang aman untuk sistem file, misalnya `Laporan_CipherLab_Kelompok_3.pdf`. Jangan mengharuskan format nama kelompok tertentu.

### PDF
Gunakan ReportLab dan buat modul khusus, misalnya `reports/pdf_report.py`. PDF harus dibuat dari data eksekusi aktual yang disimpan dalam session state atau struktur hasil bertipe, bukan dari data dummy.

Isi laporan:
1. Cover minimalis.
2. Identitas kelompok dan anggota.
3. Ringkasan status pengujian.
4. Tujuan dan deskripsi algoritma.
5. Bagian ECB, CBC, CTR terpisah.
6. Input, key, IV/counter relevan, encoding, dan parameter.
7. Tabel blok plaintext/ciphertext dalam HEX dan BIN.
8. Trace perhitungan aktual yang tersedia.
9. Hasil dekripsi dan status verifikasi.
10. Tabel perbandingan mode.
11. Kesimpulan berdasarkan hasil aktual.
12. Batasan keamanan toy cipher 16-bit.
13. Waktu pembuatan laporan.

Persyaratan kualitas:
- Layout profesional, minimalis, dengan navy/violet/cyan secukupnya.
- Nomor halaman dan footer.
- Tabel dapat membungkus teks, header berulang saat pindah halaman.
- Hindari konten yang terpotong.
- Jangan membuat ciphertext, hasil, screenshot, atau status verifikasi palsu.
- Mode yang belum dijalankan ditandai “Belum dijalankan”; jangan mengarang hasil.
- Jika verifikasi gagal, tampilkan “GAGAL” dengan jelas dan jangan menulis kesimpulan bahwa round-trip berhasil.
- Tombol unduh menghasilkan PDF langsung di browser menggunakan `st.download_button`.
- Nama file mengikuti input pengguna setelah sanitasi.
- Tidak ada API atau server eksternal untuk membuat PDF.

Tambahkan `reportlab` ke `requirements.txt` dan tes pembuatan laporan. Uji bahwa nilai di PDF cocok dengan hasil eksekusi aktual, termasuk mode yang belum dijalankan, metadata anggota, nama file, dan status verifikasi.

## 12. WORKFLOW UPDATE
Setelah fitur PDF dibuat:
- Jalankan test algoritma dan test laporan.
- Buat satu laporan dari data uji aktual saat pengembangan.
- Periksa PDF untuk layout, tabel lintas halaman, dan karakter khusus.
- Pastikan file PDF unduhan memakai nama kelompok yang diedit.
- Perbarui README dengan cara mengisi identitas dan mengunduh laporan.
