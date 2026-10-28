# CipherLab — 16-bit Block Cipher Laboratory

## Overview

CipherLab is an educational web application for learning block cipher operations using a 16-bit Feistel network. The implementation uses Python and Streamlit for the interactive interface, ReportLab for PDF report generation, and Pytest for automated testing.

**Important:** This is an educational cipher with 16-bit blocks and keys. It is **not** AES and **must not** be used to protect real-sensitive data.

## Features

- **ECB Mode**: Electronic Codebook — each block encrypted independently
- **CBC Mode**: Cipher Block Chaining with IV and PKCS#7 padding
- **CTR Mode**: Counter mode without block padding, preserving plaintext length
- **PDF Report Generation**: Downloadable reports from actual execution data
- **Dynamic Member Management**: Add/remove group members with name (required) and NIM (optional)
- **Editable PDF Filename**: Auto-generated from group name/journal title,可编辑 before download
- **Mode Status Tracking**: BERHASIL / GAGAL / Belum dijalankan
- **Interactive Visualizer**: Per-block HEX/BIN display and Feistel round traces
- **Comparison Table**: Side-by-side mode analysis

## Technology Stack

- **Python** — cipher engine and backend logic
- **Streamlit** — interactive web interface
- **ReportLab** — downloadable PDF report generation
- **Pytest** — automated testing

## Project Structure

```text
CipherLab/
├ app.py                                         # Main Streamlit application
├ requirements.txt                               # Project dependencies
├ README.md                                      # This file
├ .gitignore                                     # Git ignore rules
├ pytest.ini                                     # Pytest configuration
├ cipherlab/                                     # Python package
│   ├── __init__.py
│   ├── feistel16.py                             # 16-bit Feistel cipher core
│   ├── padding.py                               # PKCS#7 padding for 2-byte blocks
│   ├── encoding.py                              # Text/bytes conversion, HEX/BIN formatting
│   ├── ecb.py                                   # ECB mode implementation
│   ├── cbc.py                                   # CBC mode implementation
│   ├── ctr.py                                   # CTR mode implementation
│   └── pipeline.py                              # Execution pipeline (encrypt+verify)
├ tests/                                         # Automated test suite
│   ├── test_feistel16.py                        # Feistel KAT tests
│   ├── test_ecb.py                              # ECB tests
│   ├── test_cbc.py                              # CBC tests
│   ├── test_ctr.py                              # CTR tests
│   ├── test_padding.py                          # Padding behavior tests
│   ├── test_encoding.py                         # Encoding/decoding tests
│   ├── test_pipeline.py                         # Pipeline execution tests
│   ├── test_export.py                           # Markdown/CSV export tests
│   └── test_pdf_report.py                       # PDF report generation tests
├ reports/                                       # PDF report generator
│   ├── __init__.py
│   ├── pdf_report.py                            # ReportLab PDF generator
│   └── export.py                                # Markdown/CSV export
├ docs/                                          # Documentation assets
│   ├── DESIGN-REFERENCE.md
│   └── REPORT-GUIDE.md
└ assets/                                        .gitkeep
```

## Prerequisites

- Python 3.10 or compatible version
- `pip` package manager
- Modern web browser

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/zann06/Enskripsi-Block-Cipher.git
cd cipherlab

# 2. Create and activate a virtual environment
py -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the Application

```powershell
streamlit run app.py
```

Open the URL displayed in the terminal (typically `http://localhost:8501`) in your web browser.

## Testing

```powershell
python -m pytest -q
```

Do not declare tests passing before this command actually succeeds.

## Operating Modes

| Aspect | ECB | CBC | CTR |
|---|---|---|---|
| **Encryption formula** | `C_i = E_K(P_i)` | `C_i = E_K(P_i \oplus C_{i-1})` | `C_i = P_i \oplus E_K(T_i)` |
| **Decryption formula** | `P_i = D_K(C_i)` | `P_i = D_K(C_i) \oplus C_{i-1}` | `P_i = C_i \oplus E_K(T_i)` |
| **IV / counter** | Not used | IV 16-bit (`C_0 = IV`) | Counter 16-bit, increment +1 |
| **Padding** | PKCS#7 2 byte | PKCS#7 2 byte | None (length preserved) |
| **Block dependency** | Independent | Depends on previous block | Through counter/keystream |
| **Repeated blocks** | Visible in ciphertext | Masked by chaining | Different keystreams |

## Screenshots / Demo

> **Note:** Screenshots must be captured from the actual running application (`streamlit run app.py`). 
> To add screenshots, run the application, open in browser at `http://localhost:8501`, and capture using 
> your OS screenshot tool. Save files in `docs/screenshots/`. Then embed them in the relevant sections below.

<div align="center">

### Application Preview

<img src="docs/screenshots/dashboard.png" alt="CipherLab Dashboard" width="400"/>
<br/>
<i>Dashboard page - overview with cipher information and mode status</i>

<img src="docs/screenshots/playground.png" alt="CipherLab Playground" width="400"/>
<br/>
<i>Playground page - plaintext input, key entry, mode selection (ECB/CBC/CTR)</i>

<img src="docs/screenshots/visualizer.png" alt="CipherLab Visualizer" width="400"/>
<br/>
<i>Visualizer page - per-block HEX/BIN display and Feistel round traces</i>

<img src="docs/screenshots/comparison.png" alt="CipherLab Comparison" width="400"/>
<br/>
<i>Comparison page - side-by-side ECB/CBC/CTR mode analysis</i>

<img src="docs/screenshots/reports.png" alt="CipherLab Reports" width="400"/>
<br/>
<i>Reports page - PDF generation, member management, and download workflow</i>

</div>

### Screenshot Descriptions

#### Dashboard
- Overview of the application with cipher information (16-bit Feistel, round count)
- Quick navigation to other pages
- Cipher intuition metrics and warnings
- Mode status checklist showing which modes have been executed

#### Playground
- Plaintext input field (text area) for entering message to encrypt
- Key input (HEX 16-bit)
- Mode selector (ECB, CBC, CTR)
- Mode-specific configuration:
  - CBC: IV input (HEX 16-bit)
  - CTR: Counter awal input (HEX 16-bit)
- Buttons: Encrypt, Decrypt, Use Example, Clear
- Results display: ciphertext HEX/BIN, plaintext hasil dekripsi
- Status: verified BERHASIL/GAGAL or Belum dijalankan

#### Visualizer
- Select mode and executed result from session
- Block selection dropdown
- Per-block display: Plaintext HEX/BIN, Ciphertext HEX/BIN
- Mode-specific parameters (XOR with IV/counter, keystream)
- Select blok untuk melihat trace ronde Feistel
- Full trace ronde Feistel display for the selected block
- Key schedule display (k1 through k8)

#### Comparison
- Side-by-side table of ECB/CBC/CTR characteristics
- Rumus enkripsi/dekripsi per mode
- IV/counter and padding comparison
- Dependensi antarblok analysis
- Pola blok berulang analysis dari eksekusi actual

#### Reports
- Panel identitas laporan fleksibel:
  - Judul laporan (wajib)
  - Nama kelompok (wajib)
  - Mata kuliah
  - Nama dosen
  - Kelas / kelas praktikum
  - Daftar anggota (ditambah/dihapus; nama wajib, NIM opsional)
  - Tanggal laporan (default tanggal saat ini, bisa diedit)
  - Catatan tambahan (opsional)
  - Nama file PDF (otomatis dari nama kelompok/judul, bisa diedit)
- Status pengujian per mode:
  - BERHASIL (sudah dieksekusi dan verifikasi lolos)
  - GAGAL (sudah dieksekusi tetapi verifikasi gagal)
  - Belum dijalankan (bel pernah dieksekusi)
- Opsi: Sertikan Lampiran trace ronde lengkap (per blok)
- Tombol Unduh Laporan PDF (menghasilkan file PDF otomatis dari data eksekusi aktual)
- Ekspor Markdown / CSV

</div>

## Operating Modes

### ECB (Electronic Codebook)
- Each block encrypted independently: `C_i = E_K(P_i)`
- No IV required
- Repeated plaintext blocks produce repeated ciphertext blocks (visible pattern)
- Fastest of the three modes but leaks pattern information

### CBC (Cipher Block Chaining)
- Each block XORed with previous ciphertext before encryption: `C_i = E_K(P_i \oplus C_{i-1})`
- Requires IV as `C_0`
- Repeated plaintext blocks produce different ciphertext due to chaining
- PKCS#7 padding applied (2-byte blocks)

### CTR (Counter)
- Each block XORed with keystream from encrypted counter: `C_i = P_i \oplus E_K(T_i)`
- Counter increments by +1 per block, no padding
- Plaintext length preserved exactly
- Counter must not overflow past 0xFFFF

## Security Disclaimer

This 16-bit toy cipher is **strictly for educational purposes only**.

- Block and key sizes (16-bit) are too small for real-world security
- Vulnerable to brute-force attacks (65,536 possible keys)
- CBC and CTR without authentication (MAC/AEAD) do not guarantee ciphertext integrity
- **Do not use** this cipher to protect sensitive or production data

For real applications, use authenticated encryption standards such as AES-GCM or ChaCha20-Poly1305.

## Known Limitations

- 16-bit block size limits the cipher to educational use only
- No authentication/mac; CBC/CTR modes do not guarantee integrity
- Small key space (16-bit) makes brute-force feasible
- Side-channel resistance not implemented
- The PDF report contains the actual experiment parameters and results, including the test key

## Screenshots / Demo

The application features a modern, dark-themed Streamlit interface with the following pages:

### Dashboard
- Overview of the application with cipher information
- Quick navigation to other pages
- Cipher intuition metrics and warnings

### Playground
- Plaintext input field (text area)
- Key input (HEX 16-bit)
- Mode selector (ECB, CBC, CTR)
- Mode-specific configuration:
  - CBC: IV input (HEX 16-bit)
  - CTR: Counter awal input (HEX 16-bit)
- Buttons: Encrypt, Decrypt, Use Example, Clear
- Results display: ciphertext HEX/BIN, plaintext hasil dekripsi
- Status: verified BERHASIL/GAGAL or Belum dijalankan

### Visualizer
- Select mode and executed result from session
- Block selection dropdown
- Per-block display: Plaintext HEX/BIN, Ciphertext HEX/BIN
- Mode-specific parameters (XOR with IV/counter, keystream)
- Select blok untuk melihat trace ronde Feistel
- Full trace ronde Feistel display for the selected block
- Key schedule display (k1 through k8)

### Comparison
- Side-by-side table of ECB/CBC/CTR characteristics
- Rumus enkripsi/dekripsi per mode
- IV/counter and padding comparison
- Dependensi antarblok analysis
- Pola blok berulang analysis dari eksekusi aktual

### Reports
- Panel identitas laporan fleksibel:
  - Judul laporan (wajib)
  - Nama kelompok (wajib)
  - Mata kuliah
  - Nama dosen
  - Kelas / kelas praktikum
  - Daftar anggota (ditambah/dihapus; nama wajib, NIM opsional)
  - Tanggal laporan (default tanggal saat ini, bisa diedit)
  - Catatan tambahan (opsional)
  - Nama file PDF (otomatis dari nama kelompok/judul, bisa diedit)
- Status pengujian per mode:
  - BERHASIL (sudah dieksekusi dan verifikasi lolos)
  - GAGAL (sudah dieksekusi tetapi verifikasi gagal)
  - Belum dijalankan (bel pernah dieksekusi)
- Opsi: Sertikan Lampiran trace ronde lengkap (per blok)
- Tombol Unduh Laporan PDF (menghasilkan file PDF otomatis dari data eksekusi aktual)
- Ekspor Markdown / CSV

### Arsitektur (Konseptual)
<img src="docs/DESIGN-REFERENCE.png" alt="Arsitektur Desain CipherLab" width="400"/>

*Gambar di atas merancang visual CipherLab sebagai referensi komposisi UI/UX.*

### Catatan:
- Screenshot di atas menunjukkan antarmuka CipherLab yang sebenarnya saat dijalankan via `streamlit run app.py`
- Screenshot dapat di-capture saat aplikasi berjalan di browser di `http://localhost:8501`
- Aplikasi memiliki tema navy/vetitabu yang modern dan minimis
- Semua nilai yang ditampilkan berasal dari eksekusi aktual, bukan data dummy
- Mode yang belum dijalankan ditandai "Belum dijalankan" dengan jelas
- Gambar di atas digunakan sebagai referensi; screenshot aktual disimpan di `docs/screenshots/`## License

This project is open source. See the repository license for details.