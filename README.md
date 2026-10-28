# CipherLab — Block Cipher Playground

CipherLab adalah aplikasi web edukasi berbasis Python + Streamlit untuk mempelajari enkripsi dan dekripsi block cipher dengan mode ECB, CBC, dan CTR menggunakan ukuran blok 16 bit (2 byte).

> **Peringatan:** Jika menggunakan toy Feistel 16-bit, algoritma tersebut hanya untuk pembelajaran dan tidak aman untuk melindungi data nyata. AES memiliki ukuran blok 128 bit, bukan 16 bit.

## Fitur yang Direncanakan

- Playground enkripsi dan dekripsi.
- Pilihan ECB, CBC, dan CTR.
- Tampilan HEX dan biner per blok.
- Visualisasi XOR, IV/chaining, counter, dan keystream.
- Verifikasi hasil dekripsi.
- Perbandingan mode.
- **Ekspor laporan PDF** (berhasil diimplementasikan).
- Unit test untuk algoritma dan mode.

Fitur di atas dianggap selesai setelah benar-benar diimplementasikan dan diuji.

## Persyaratan

- Python 3.11 atau versi kompatibel.
- `pip`.
- Browser modern.

## Instalasi di Windows PowerShell

```powershell
git clone <URL-REPOSITORY-ANDA>
cd cipherlab

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika PowerShell memblokir aktivasi virtual environment, gunakan Command Prompt atau periksa kebijakan eksekusi yang berlaku pada perangkatmu. Jangan mengubah kebijakan keamanan komputer kampus tanpa izin.

## Menjalankan aplikasi

```powershell
streamlit run app.py
```

Buka URL lokal yang ditampilkan di terminal, biasanya `http://localhost:8501`.

## Menjalankan test

Jika proyek menggunakan pytest:

```powershell
python -m pytest -q
```

Jangan menyatakan test lulus sebelum perintah tersebut benar-benar berhasil.

## Mode Operasi

- **ECB:** setiap blok diproses secara independen.
- **CBC:** plaintext di-XOR dengan IV atau ciphertext sebelumnya sebelum enkripsi.
- **CTR:** plaintext di-XOR dengan keystream yang diperoleh dari enkripsi counter block.

## Batasan Keamanan

Cipher 16-bit edukasional tidak boleh dipakai untuk data sensitif atau produksi. Mode CBC dan CTR tanpa mekanisme autentikasi (MAC/AEAD) tidak menjamin integritas ciphertext. Untuk aplikasi nyata, gunakan pustaka kriptografi teruji dan konstruksi authenticated encryption yang sesuai, bukan implementasi toy cipher ini.

## Struktur Proyek

```text
cipherlab/
├ app.py
├ crypto/
│   ├── __init__.py
│   ├── feistel16.py
│   ├── ecb.py
│   ├── cbc.py
│   ├── ctr.py
│   ├── padding.py
│   └── encoding.py
├ tests/
│   ├── test_feistel16.py
│   ├── test_ecb.py
│   ├── test_cbc.py
│   ├── test_ctr.py
│   ├── test_padding.py
│   ├── test_encoding.py
│   ├── test_pipeline.py
│   ├── test_export.py
│   ├── test_pdf_report.py
│   └── ref_impl.py
├ reports/
│   ├── __init__.py
│   ├── pdf_report.py
│   └── export.py
├ PRD.md
├ PROMPT.md
├ README.md
├ requirements.txt
└── .gitignore
```

## Dokumen Pendamping

- `PRD.md` — persyaratan produk dan algoritma.
- `PROMPT.md` — prompt implementasi untuk OpenCode.
- `docs/design-reference.png` — referensi visual bila disertikan.

## Kontribusi

Perubahan algoritma harus disertai penjelasan, test independen, dan pembaruan dokumentasi. Jangan mengklaim keamanan kriptografis tanpa analisis dan validasi yang layak.

## Lisensi

Pilih lisensi open-source sebelum publikasi, misalnya MIT, setelah memastikan seluruh dependensi dan aset memiliki lisensi yang sesuai.

## Laporan PDF Otomatis

CipherLab dirancang untuk membuat laporan PDF detail dari hasil eksekusi aktual.

Pada halaman **Reports - Laporan**:

1. Isi identitas kelompok: judul laporan, nama kelompok, mata kuliah, dosen, kelas, tanggal, dan daftar anggota.
2. Jalankan ECB, CBC, dan CTR di Playground terlebih dahulu.
3. Periksa status verifikasi dan tabel per blok.
4. Atur nama file PDF jika diperlukan.
5. Klik **Unduh Laporan PDF**.

Nama kelompok dan anggota tidak di-hardcode. Nama file otomatis mengikuti nama kelompok/judul, lalu dapat disunting. Mode yang belum dijalankan ditandai jelas di PDF; PDF tidak mengarang hasil.

PDF berisi identitas kelompok, ringkasan, parameter, hasil tiap mode, tabel HEX/BIN per blok, trace yang tersedia, hasil dekripsi, status verifikasi, perbandingan, dan batasan keamanan.

Dependensi PDF: ReportLab. Pembuatan PDF berjalan lokal tanpa API eksternal. Fitur ini dianggap selesai setelah modul dan tombol unduh benar-benar diimplementasikan dan diuji.

### Fitur Halaman Reports

Panel identitas laporan fleksibel:

- **Judul laporan** (wajib)
- **Nama kelompok** (wajib)
- **Mata kuliah**
- **Nama dosen**
- **Kelas / kelas praktikum**
- **Daftar anggota** yang dapat ditambah/dihapus; nama wajib, NIM opsional
- **Tanggal laporan** (default tanggal saat ini, bisa diedit)
- **Catatan tambahan** (opsional)
- **Nama file PDF** (otomatis dari nama kelompok/judul, tetapi bisa diedit sebelum unduh)

Daftar anggota dinamis:
- Tambah baris anggota baru
- Hapus anggota yang sudah ada
- Setiap anggota memiliki field nama (wajib) dan NIM (opsional)

Status mode di halaman Reports:

- Mode yang sudah dieksekusi dan verifikasi lolos ditandai "BERHASIL"
- Mode yang sudah dieksekusi tetapi verifikasi gagal ditandai "GAGAL"
- Mode yang belum pernah dijalankan ditandai "Belum dijalankan" dengan jelas

Tombol unduh PDF aktif setelah setidaknya satu mode dieksekusi. Untuk laporan tugas yang lengkap, anjurkan ketiga mode (ECB, CBC, CTR) harus dijalankan dan lolos verifikasi.

Isi PDF sesuai hasil eksekusi aktual dari aplikasi, tidak ada data dummy:
- Cover: judul laporan, nama kelompok, mata kuliah, dosen, kelas, tanggal, daftar anggota
- Ringkasan eksekusi: cipher inti, block size 16 bit, mode yang dijalankan, status verifikasi
- Parameter per mode: kunci, IV (CBC) / counter awal (CTR), encoding, padding
- Tabel per blok: plaintext HEX/BIN, ciphertext HEX/BIN, parameter XOR/counter/keystream per mode
- Trace perhitungan Feistel per blok (opsional/dapat dilampir)
- Hasil dekripsi dan status verifikasi per mode
- Tabel perbandingan mode ECB/CBC/CTR
- Kesimpulan berdasarkan data eksekusi aktual (tidak dimarag)
- Batasan dan peringatan keamanan toy cipher 16-bit