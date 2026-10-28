# CipherLab — Product Requirements Document (PRD)

**Versi:** 1.0  
**Jenis:** Proyek edukasi / tugas kuliah  
**Bahasa implementasi:** Python  
**Antarmuka:** Streamlit (web app)  
**Mode:** ECB, CBC, CTR  
**Ukuran blok:** 16 bit (2 byte)

## 1. Ringkasan

CipherLab adalah aplikasi web edukasi untuk mempelajari dan menjalankan enkripsi/dekripsi block cipher berukuran 16 bit. Pengguna dapat memilih mode ECB, CBC, atau CTR, melihat hasil per blok dalam HEX dan biner, menelusuri alur perhitungan, memverifikasi dekripsi, membandingkan karakteristik mode, dan mengekspor laporan.

Aplikasi dijalankan lokal melalui browser menggunakan Streamlit. Tidak diperlukan backend terpisah, database, akun, atau API berbayar.

## 2. Latar Belakang dan Tujuan

Tugas meminta program enkripsi dan dekripsi block cipher dengan mode ECB, CBC, dan Counter serta ukuran blok 16 bit, disertai laporan hasil eksekusi tiap mode.

Tujuan produk:
- Menyediakan implementasi yang benar dan mudah diaudit.
- Menjelaskan bagaimana blok diproses pada setiap mode.
- Menyediakan bukti hasil eksekusi yang dapat dimasukkan ke laporan tugas.
- Menjadi proyek open-source edukasional yang rapi dan mudah dijalankan.

## 3. Target Pengguna

- Mahasiswa yang mempelajari kriptografi.
- Dosen atau asisten praktikum yang mendemonstrasikan mode operasi.
- Pemula yang ingin memahami hubungan antara plaintext, key, IV/counter, dan ciphertext.

## 4. Keputusan Algoritma

Ukuran blok 16 bit **tidak berarti AES**. AES menggunakan blok 128 bit. Jika dosen tidak menentukan cipher inti tertentu, gunakan **toy Feistel Network 16-bit** yang reversible, didokumentasikan, dan ditujukan hanya untuk pembelajaran. Jika dosen menentukan algoritma lain, ikuti spesifikasi dosen dan ubah PRD sebelum implementasi.

Spesifikasi awal:
- Blok: 16 bit = 2 byte.
- Kunci: 16 bit untuk toy cipher awal.
- Cipher inti: Feistel 8 ronde, dengan fungsi ronde dan key schedule deterministik yang terdokumentasi.
- Implementasikan `encrypt_block()` dan `decrypt_block()` sebagai fungsi invers.
- Jangan menggunakan XOR plaintext-key sebagai satu-satunya “cipher”.
- Jangan menyebut toy cipher sebagai standar atau aman untuk data nyata.

## 5. Pengguna dan Alur Utama

1. Pengguna membuka Dashboard.
2. Pengguna masuk ke Playground.
3. Pengguna memasukkan plaintext dan kunci.
4. Pengguna memilih ECB, CBC, atau CTR.
5. Untuk CBC, pengguna memasukkan IV; untuk CTR, pengguna memasukkan initial counter.
6. Pengguna menjalankan Encrypt.
7. Aplikasi menampilkan ciphertext HEX/BIN dan jejak perhitungan per blok.
8. Pengguna menjalankan Decrypt dan memverifikasi hasilnya.
9. Pengguna membuka Reports dan mengunduh laporan.

## 6. Fitur dan Persyaratan Fungsional

### P0 — wajib
- **Dashboard:** menjelaskan CipherLab, cipher inti, ukuran blok, dan tautan halaman.
- **Playground:** input plaintext, key, mode, IV/counter sesuai mode, Encrypt, Decrypt, Clear, dan contoh input.
- **Enkripsi/dekripsi:** implementasi aktual ECB, CBC, dan CTR, bukan hasil hardcoded.
- **Representasi:** tampilkan blok 16-bit, HEX, dan biner.
- **Visualizer:** tampilkan operasi per blok, termasuk XOR dan chaining/keystream.
- **Verifikasi:** hasil dekripsi harus cocok dengan plaintext asli setelah penanganan padding/encoding.
- **Validasi:** pesan kesalahan jelas untuk key, IV, counter, encoding, dan input yang tidak valid.
- **Pengujian:** unit test cipher inti dan seluruh mode.
- **Dokumentasi:** README, batasan keamanan, cara instalasi dan menjalankan aplikasi.

### P1 — disarankan
- Halaman Comparison dengan tabel ECB/CBC/CTR.
- Ekspor laporan Markdown dan CSV.
- Trace ronde Feistel untuk blok yang dipilih.
- Contoh plaintext yang bisa dimuat dengan satu klik.
- Navigasi dan layout responsif.

### Di luar cakupan
- Akun pengguna, database, penyimpanan cloud.
- Enkripsi data produksi.
- Integrasi API AI.
- Klaim bahwa toy cipher memberikan keamanan nyata.

## 7. Spesifikasi Mode Operasi

Notasi: `E_K` = enkripsi satu blok dengan kunci K, `D_K` = dekripsi satu blok, `P_i` = blok plaintext, `C_i` = blok ciphertext, `⊕` = XOR.

### ECB
- Enkripsi: `C_i = E_K(P_i)`.
- Dekripsi: `P_i = D_K(C_i)`.
- Tiap blok diproses independen.
- Tidak menggunakan IV.
- ECB memperlihatkan pola saat blok plaintext berulang.

### CBC
- Enkripsi: `C_i = E_K(P_i ⊕ C_(i-1))`, dengan `C_0 = IV`.
- Dekripsi: `P_i = D_K(C_i) ⊕ C_(i-1)`.
- Menggunakan IV 16-bit.
- Tiap blok ciphertext bergantung pada blok sebelumnya.

### CTR
- Keystream: `S_i = E_K(T_i)`.
- Enkripsi: `C_i = P_i ⊕ S_i`.
- Dekripsi: `P_i = C_i ⊕ S_i`.
- `T_i` adalah counter block 16-bit yang bertambah sesuai aturan yang terdokumentasi.
- Tidak membutuhkan padding; panjang plaintext dipertahankan.
- Validasi agar counter tidak wrap/overflow.

## 8. Encoding dan Padding

- Teks dikonversi menjadi byte UTF-8.
- Blok berukuran 2 byte.
- ECB dan CBC menggunakan PKCS#7 yang disesuaikan dengan block size 2 byte, termasuk penanganan input kosong.
- CTR tidak menggunakan padding.
- Simpan metadata panjang byte asli pada sesi eksekusi agar hasil dekripsi dan ekspor dapat mengembalikan plaintext dengan benar.
- Tampilkan HEX dan biner per blok.
- Jangan diam-diam mengubah input pengguna.

## 9. Desain UI/UX

### Prinsip
- Modern, minimalis, teknis, mudah dibaca.
- Prioritaskan visualisasi dan data dibanding dekorasi.
- Tidak ada badge dekoratif berlebihan, statistik palsu, atau animasi yang mengganggu.
- Seluruh tombol utama berfungsi.

### Palet
- Background: `#0B1020`
- Surface: `#151C30`
- Primary violet: `#8B5CF6`
- Accent cyan: `#22D3EE`
- Text: `#F3F4F6`
- Muted: `#94A3B8`
- Success: gunakan warna hijau secukupnya untuk status verifikasi.

### Tipografi
- UI: Inter atau font sans-serif sistem.
- Data HEX/BIN/key: monospace.
- Spasi konsisten, panel sederhana, border halus, radius 10–14 px.
- Pastikan kontras dan navigasi keyboard tetap baik.

### Halaman
1. Dashboard
2. Playground
3. Visualizer
4. Comparison
5. Reports

Streamlit memiliki batasan dalam layout dan interaksi kompleks; utamakan komponen native Streamlit. Jangan mengklaim animasi/fitur yang belum diimplementasikan.

## 10. Tech Stack

- Python 3.11 atau versi stabil yang kompatibel.
- Streamlit untuk UI.
- Pandas hanya jika diperlukan untuk tabel.
- Pytest untuk testing (atau unittest bila menjaga dependensi minimal).
- Tidak perlu database atau backend API.
- `requirements.txt` harus mencantumkan dependensi yang benar-benar dipakai.

## 11. Struktur Proyek yang Disarankan

```text
cipherlab/
├── app.py
├── crypto/
│   ├── __init__.py
│   ├── feistel16.py
│   ├── ecb.py
│   ├── cbc.py
│   ├── ctr.py
│   ├── padding.py
│   └── encoding.py
├── tests/
│   ├── test_feistel16.py
│   ├── test_ecb.py
│   ├── test_cbc.py
│   └── test_ctr.py
├── docs/
│   └── design-reference.png
├── PRD.md
├── PROMPT.md
├── README.md
├── requirements.txt
└── .gitignore
```

## 12. Kriteria Penerimaan

- [ ] Ketiga mode dapat melakukan enkripsi dan dekripsi.
- [ ] Cipher inti reversible untuk semua blok 16-bit pada kunci uji yang valid.
- [ ] Hasil dekripsi sama dengan plaintext awal untuk input yang didukung.
- [ ] ECB tidak meminta IV; CBC meminta IV; CTR meminta counter.
- [ ] Visualizer menampilkan perhitungan aktual, bukan nilai contoh hardcoded.
- [ ] Error input ditampilkan dengan jelas.
- [ ] Ada pengujian unit untuk cipher dan tiap mode.
- [ ] Laporan dapat diekspor dan berasal dari hasil eksekusi aktual.
- [ ] Aplikasi bisa dijalankan dengan `streamlit run app.py`.
- [ ] README menjelaskan batasan keamanan dan setup dari nol.

## 13. Risiko dan Batasan

- Toy cipher 16-bit tidak aman untuk data nyata; ini hanya untuk edukasi.
- Mode CBC/CTR tanpa autentikasi tidak menjamin integritas ciphertext.
- IV/nonce/counter harus dikelola dengan benar dalam penggunaan nyata.
- Jika spesifikasi dosen berbeda, spesifikasi dosen harus diprioritaskan.
- Output dan test vector harus benar-benar diverifikasi, bukan dibuat-buat.

## 14. Definition of Done

Aplikasi selesai jika implementasi cipher, tiga mode, visualisasi, pengujian, ekspor laporan, dokumentasi, dan alur utama berjalan. Catat hasil test yang benar-benar dijalankan dan laporkan keterbatasan yang belum diselesaikan.


## 15. Laporan PDF Otomatis — Persyaratan Tambahan

### Tujuan
Setelah kelompok menjalankan pengujian ECB, CBC, dan CTR, aplikasi harus menyediakan halaman **Laporan** yang membuat laporan PDF detail dari data eksekusi aktual. PDF bukan template kosong: hasil, parameter, tabel blok, dan status verifikasi harus diambil dari hasil komputasi aplikasi yang sedang/sudah dijalankan.

### Metadata yang bisa diatur kelompok
Sediakan panel **Identitas Laporan** dengan input:
- Nama/judul laporan (wajib).
- Nama kelompok (wajib).
- Nama mata kuliah.
- Nama dosen.
- Kelas/kelas praktikum.
- Daftar anggota kelompok yang dapat ditambah/dihapus, dengan nama dan NIM opsional.
- Tanggal laporan (default tanggal saat ini, bisa diedit).
- Catatan tambahan (opsional).
- Nama file PDF (otomatis dari nama kelompok/judul, tetapi bisa diedit sebelum unduh).

Jangan hardcode nama kelompok atau anggota tertentu. Semua metadata diisi pengguna dan bisa diperbarui sebelum ekspor. Sanitasi nama file untuk menghapus karakter yang tidak aman; gunakan nama default seperti `Laporan_CipherLab_<NamaKelompok>.pdf`.

### Isi PDF
PDF final menggunakan layout minimalis dan profesional:
1. Cover: judul laporan, nama kelompok, mata kuliah, dosen, kelas, tanggal, daftar anggota.
2. Ringkasan eksekusi: cipher inti, block size 16 bit, mode yang berhasil dijalankan, dan status verifikasi.
3. Tujuan dan ruang lingkup.
4. Penjelasan singkat algoritma dan rumus ECB/CBC/CTR.
5. Bagian terpisah untuk ECB, CBC, dan CTR yang benar-benar dieksekusi:
   - metadata mode dan parameter relevan;
   - plaintext asli dan encoding;
   - key (tampilkan dengan aman sesuai kebutuhan akademik; beri peringatan bahwa ini toy cipher edukasional);
   - IV untuk CBC atau initial counter untuk CTR;
   - blok input dan ciphertext dalam HEX/BIN;
   - trace perhitungan yang tersedia dari implementasi;
   - plaintext hasil dekripsi;
   - status verifikasi `BERHASIL`/`GAGAL`;
   - screenshot bukan kewajiban jika semua data disajikan dalam tabel, tetapi boleh ada area bukti/visualisasi bila tersedia.
6. Tabel perbandingan mode.
7. Analisis dan kesimpulan yang dibuat dari data eksekusi, tanpa mengarang temuan.
8. Batasan dan peringatan keamanan.
9. Lampiran parameter/test yang relevan.

### Aturan pembuatan laporan
- Ekspor hanya data aktual dari eksekusi, jangan gunakan ciphertext atau trace hardcoded.
- Beri peringatan jika salah satu mode belum pernah dijalankan atau gagal verifikasi.
- Default: tombol unduh PDF aktif setelah tersedia setidaknya satu eksekusi; tampilkan checklist mode yang sudah/belum diuji. Untuk laporan lengkap tugas, anjurkan ketiga mode harus lulus verifikasi.
- PDF harus dapat dibuat tanpa layanan eksternal/API.
- Gunakan ReportLab untuk PDF. Jika ReportLab tidak tersedia, tampilkan pesan instalasi yang jelas; jangan diam-diam membuat file palsu.
- Gunakan nama file yang diatur pengguna dan slug aman.
- Sertakan timestamp pembuatan laporan.
- Pastikan tabel panjang membungkus teks dan berlanjut ke halaman berikutnya dengan header tabel berulang.
- Jangan memotong data trace penting secara diam-diam; boleh ringkas trace per ronde dengan opsi lampiran lengkap.
- Jangan menyertakan secret apa pun selain input akademik yang memang dimasukkan pengguna; jelaskan bahwa laporan menyimpan parameter uji yang dipilih.

### Kriteria penerimaan PDF
- [ ] Identitas kelompok bisa diisi dan diubah.
- [ ] Daftar anggota bisa ditambah/dihapus.
- [ ] Nama file otomatis mengikuti kelompok/judul dan dapat diedit.
- [ ] PDF memuat hasil aktual ECB, CBC, CTR yang sudah dijalankan.
- [ ] Tabel blok memuat data yang sama dengan UI.
- [ ] Status verifikasi sesuai hasil aktual.
- [ ] Mode yang belum dijalankan ditandai dengan jelas.
- [ ] Layout minimalis, terbaca, dan tidak memotong tabel.
- [ ] PDF dapat diunduh dari browser lokal tanpa API eksternal.
- [ ] Pengujian memastikan konten laporan cocok dengan objek hasil eksekusi.

