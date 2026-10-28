# CipherLab — Laboratorium Kriptografi Block Cipher 16-bit

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b.svg)](https://streamlit.io/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF-orange.svg)](https://www.reportlab.com/)
[![Pytest](https://img.shields.io/badge/Pytest-Passing-green.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Aplikasi web dan laboratorium edukasi untuk mengeksplorasi operasi block cipher menggunakan jaringan Feistel 16-bit kustom.*

</div>

---

## Tentang Aplikasi

**CipherLab** adalah perangkat lunak berbasis web dan laboratorium kriptografi interaktif yang dirancang khusus untuk kebutuhan pembelajaran mata kuliah Kriptografi dan Keamanan Informasi. Aplikasi ini mengimplementasikan jaringan Feistel 16-bit yang sederhana namun komprehensif, memungkinkan mahasiswa dan praktisi untuk mempelajari secara mendalam cara kerja internal dari operasi *block cipher* serta mode-mode pengoperasian standarnya.

Melalui antarmuka berbasis Streamlit yang responsif dan modern, pengguna dapat:
- Melakukan enkripsi dan dekripsi menggunakan mode **ECB (Electronic Codebook)**, **CBC (Cipher Block Chaining)**, dan **CTR (Counter Mode)**.
- Menelusuri proses internal per blok secara transparan (representasi HEX dan Biner).
- Mengamati proses penjadwalan kunci ($k_1$ hingga $k_8$) serta ronde Feistel langkah demi langkah.
- Memverifikasi hasil eksekusi secara otomatis dan menyusun laporan praktikum profesional berformat PDF secara instan menggunakan ReportLab.

> **Peringatan Keamanan Penting:** Cipher ini merupakan cipher edukasi dengan blok dan kunci berukuran 16-bit. Cipher ini **bukan** AES dan **tidak boleh** digunakan untuk melindungi data sensitif di dunia nyata.

---

## Fitur Utama

- **3 Mode Operasi**:
  - **Mode ECB**: *Electronic Codebook* — enkripsi blok independen dengan padding PKCS#7.
  - **Mode CBC**: *Cipher Block Chaining* — pengaitan blok dengan IV dan padding PKCS#7.
  - **Mode CTR**: *Counter Mode* — operasi seperti *stream cipher* tanpa padding, mempertahankan panjang *plaintext*.
- **Visualisator Interaktif**: Inspeksi HEX/BIN per blok dan penelusuran ronde Feistel langkah demi langkah ($k_1$ hingga $k_8$).
- **Tabel Perbandingan Samping-Menyamping**: Analisis langsung terkait rumus, penggunaan IV/counter, padding, dan dependensi antarblok.
- **Laporan PDF Profesional**: Membuat dan mengunduh laporan eksekusi lengkap menggunakan ReportLab langsung dari *session state* aplikasi.
- **Manajemen Anggota Kelompok Dinamis**: Menambah atau menghapus anggota kelompok dengan nama (wajib) dan NIM (opsional).
- **Nama File PDF Kustom**: Nama file PDF otomatis yang dapat disesuaikan sebelum diunduh.
- **Pelacakan Status Real-time**: Label status otomatis (`BERHASIL`, `GAGAL`, `Belum dijalankan`) per mode.

---

## Struktur Proyek

```text
CipherLab/
├── app.py                          # Aplikasi utama Streamlit
├── requirements.txt                # Dependensi pustaka Python
├── README.md                       # Dokumentasi proyek
├── pytest.ini                      # Konfigurasi Pytest
├── crypto/                         # Mesin inti kriptografi
│   ├── __init__.py
│   ├── feistel16.py                # Inti cipher Feistel 16-bit & penjadwalan kunci
│   ├── padding.py                  # Padding PKCS#7 untuk blok 2-byte
│   ├── encoding.py                 # Konversi teks/bytes, pemformatan HEX/BIN
│   ├── ecb.py                      # Implementasi mode ECB
│   ├── cbc.py                      # Implementasi mode CBC
│   ├── ctr.py                      # Implementasi mode CTR
│   ├── pipeline.py                 # Pipa eksekusi (enkripsi + verifikasi)
│   └── results.py                  # Struktur data hasil
├── reports/                        # Generator laporan PDF dan eksportir
│   ├── __init__.py
│   ├── pdf_report.py               # Generator PDF ReportLab
│   └── export.py                   # Utilitas ekspor Markdown / CSV
├── tests/                          # Suite pengujian otomatis yang komprehensif
│   ├── test_feistel16.py           # Pengujian Feistel KAT & ronde
│   ├── test_ecb.py                 # Pengujian mode ECB
│   ├── test_cbc.py                 # Pengujian mode CBC
│   ├── test_ctr.py                 # Pengujian mode CTR
│   ├── test_padding.py             # Pengujian perilaku padding
│   ├── test_encoding.py            # Pengujian utilitas encoding
│   ├── test_pipeline.py            # Pengujian verifikasi pipa eksekusi
│   ├── test_export.py              # Pengujian ekspor
│   └── test_pdf_report.py          # Pengujian pembuatan laporan PDF
└── docs/                           # Dokumentasi dan aset
    ├── DESIGN-REFERENCE.md
    ├── REPORT-GUIDE.md
    ├── contoh-laporan.pdf          # Contoh laporan PDF yang dihasilkan
    └── screenshots/                # Tangkapan layar aplikasi
        ├── dashboard.png
        ├── playground.png
        ├── playground-lanjutan.png
        ├── visualizer.png
        ├── comparison.png
        └── reports.png
```

---

## Memulai (Getting Started)

### Prasyarat

- Python 3.10 atau versi yang kompatibel
- Manajer paket `pip`

### Instalasi

```powershell
# 1. Kloning repositori
git clone https://github.com/zann06/Enskripsi-Block-Cipher.git
cd Enskripsi-Block-Cipher

# 2. Buat dan aktifkan lingkungan virtual (virtual environment)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Instal dependensi
pip install -r requirements.txt
```

### Menjalankan Aplikasi

```powershell
streamlit run app.py
```

Buka URL lokal yang ditampilkan di terminal (biasanya `http://localhost:8501`) pada peramban web Anda.

### Menjalankan Pengujian (Testing)

```powershell
python -m pytest -v
```

---

## Tangkapan Layar Aplikasi

Berikut adalah pratinjau antarmuka pengguna CipherLab pada halaman-halaman utamanya:

### 1. Halaman Dasbor (Dashboard)
Gambaran umum cipher Feistel 16-bit, kartu navigasi cepat, dan daftar periksa status eksekusi mode langsung.
<div align="center">
  <img src="docs/screenshots/dashboard.png" alt="Pratinjau Dashboard" width="85%"/>
</div>

### 2. Halaman Playground (Input & Eksekusi)
Input *plaintext*, konfigurasi kunci HEX 16-bit, pemilihan mode (ECB, CBC, CTR), dan hasil kriptografi.
<div align="center">
  <img src="docs/screenshots/playground.png" alt="Pratinjau Playground" width="85%"/>
</div>

### 3. Halaman Playground Lanjutan (Konfigurasi Lanjutan & Dekripsi)
Parameter lanjutan seperti konfigurasi IV dan *Counter* awal beserta status verifikasi dekripsi.
<div align="center">
  <img src="docs/screenshots/playground-lanjutan.png" alt="Pratinjau Playground Lanjutan" width="85%"/>
</div>

### 4. Halaman Visualisator (Visualizer)
Inspeksi per blok yang menampilkan transformasi HEX/BIN, langkah XOR, dan penelusuran ronde Feistel lengkap ($k_1 - k_8$).
<div align="center">
  <img src="docs/screenshots/visualizer.png" alt="Pratinjau Visualisator" width="85%"/>
</div>

### 5. Halaman Perbandingan (Comparison)
Tabel perbandingan analitis berdampingan yang merinci rumus, padding, penggunaan IV, dan perilaku dependensi blok.
<div align="center">
  <img src="docs/screenshots/comparison.png" alt="Pratinjau Perbandingan" width="85%"/>
</div>

### 6. Halaman Laporan (Reports)
Manajemen anggota kelompok, pengeditan nama file PDF kustom, dan pembuatan laporan PDF sekali klik.
<div align="center">
  <img src="docs/screenshots/reports.png" alt="Pratinjau Laporan" width="85%"/>
</div>

---

## Contoh Laporan PDF

Anda dapat memeriksa contoh laporan PDF yang telah dibuat sebelumnya langsung dari hasil eksekusi aplikasi aktual:

- **[Unduh / Lihat Contoh Laporan PDF (docs/contoh-laporan.pdf)](docs/contoh-laporan.pdf)**

---

## Perbandingan Mode Operasi

| Aspek | ECB (Electronic Codebook) | CBC (Cipher Block Chaining) | CTR (Counter Mode) |
| :--- | :--- | :--- | :--- |
| **Rumus Enkripsi** | $C_i = E_K(P_i)$ | $C_i = E_K(P_i \oplus C_{i-1})$ | $C_i = P_i \oplus E_K(T_i)$ |
| **Rumus Dekripsi** | $P_i = D_K(C_i)$ | $P_i = D_K(C_i) \oplus C_{i-1}$ | $P_i = C_i \oplus E_K(T_i)$ |
| **IV / Counter** | Tidak diperlukan | IV 16-bit ($C_0 = \text{IV}$) | Counter 16-bit (kenaikan +1) |
| **Padding** | PKCS#7 (blok 2-byte) | PKCS#7 (blok 2-byte) | Tidak ada (Panjang tetap terjaga) |
| **Dependensi Blok** | Blok independen | Terikat dengan *ciphertext* sebelumnya | *Keystream* melalui *counter* |
| **Kebocoran Pola** | Terlihat pada blok berulang | Disamarkan dengan pengaitan | Disamarkan dengan *keystream* |

---

## Tumpukan Teknologi (Technology Stack)

- **Python**: Mesin inti kriptografi dan logika pipa.
- **Streamlit**: Antarmuka web interaktif yang responsif dengan tema gelap.
- **ReportLab**: Pembuatan laporan PDF terprogram secara profesional.
- **Pytest**: Suite pengujian otomatis yang ketat mencakup KAT dan kasus batas (*edge cases*).

---

## Lisensi

Proyek ini bersumber terbuka dan tersedia di bawah [Lisensi MIT](LICENSE).
