# Design Reference — CipherLab

## Arah visual

**Kata kunci:** modern, minimalis, dark laboratory, teknis, mudah dibaca, berorientasi data.

Gunakan gambar `design-reference.png` sebagai inspirasi komposisi. Jangan menempel gambar sebagai pengganti UI asli; bangun setiap komponen menggunakan Streamlit.

## Design tokens

| Token | Nilai | Penggunaan |
|---|---|---|
| Background | `#0B1020` | Latar utama |
| Surface | `#151C30` | Panel dan kartu |
| Primary | `#8B5CF6` | Tombol utama, tab aktif |
| Accent | `#22D3EE` | Highlight alur dan visualisasi |
| Text | `#F3F4F6` | Teks utama |
| Muted | `#94A3B8` | Label dan teks sekunder |
| Border | `#293650` | Garis pemisah halus |

## Tipografi

- UI: Inter jika tersedia, fallback sans-serif sistem.
- Data teknis: monospace.
- HEX/BIN/key/counter harus memiliki alignment yang konsisten.
- Hindari ukuran teks terlalu kecil.

## Layout

### Sidebar
- Logo dan nama CipherLab.
- Navigasi: Dashboard, Playground, Visualizer, Comparison, Reports.
- Keterangan singkat “Educational project · 16-bit blocks”.
- Sidebar ringkas, tidak penuh dekorasi.

### Dashboard
- Headline: “Belajar block cipher secara visual.”
- Deskripsi singkat.
- Ringkasan ukuran blok, cipher edukasional, dan tiga mode.
- Quick actions menuju Playground dan Visualizer.
- Jangan tampilkan statistik penggunaan palsu.

### Playground
- Panel input: plaintext, key 16-bit, mode, IV atau counter sesuai mode.
- Panel hasil: ciphertext HEX/BIN, plaintext hasil dekripsi, status verifikasi.
- Tombol utama: Encrypt, Decrypt, Clear, Use Example.
- Label input eksplisit dan pesan error yang membantu.

### Visualizer
- Tabel blok plaintext/ciphertext.
- Diagram alur per mode.
- CBC menampilkan IV atau ciphertext sebelumnya dan XOR.
- CTR menampilkan counter block dan keystream.
- Trace ronde Feistel jika tersedia.
- Sorot blok aktif secara halus; jangan bergantung pada warna saja.

### Comparison
- Tabel ECB/CBC/CTR.
- Bandingkan dependensi antarblok, IV/counter, padding, pola blok identik, dan batasan keamanan.
- Catatan jelas: mode dasar tidak otomatis menyediakan autentikasi.

### Reports
- Parameter eksekusi.
- Hasil per blok.
- Ciphertext dan hasil dekripsi.
- Status verifikasi.
- Tombol unduh Markdown dan CSV.

## Prinsip UX

- Minimal badge; hanya untuk status penting seperti “Berhasil diverifikasi”.
- Jangan gunakan glow berlebihan atau gradient pada semua panel.
- Spacing konsisten dan panel dengan border halus.
- Tabel teknis lebih penting daripada animasi.
- Semua tombol harus melakukan aksi yang jelas.
- Layout tetap usable pada lebar layar kecil.
- Berikan penjelasan saat input salah.
- Data hasil harus berasal dari algoritma yang benar-benar dijalankan.

## Batasan Streamlit

Streamlit cocok untuk tugas dan demo web lokal. Jika animasi kompleks tidak diperlukan, jangan menambahkan framework frontend terpisah. Utamakan komponen native Streamlit, CSS ringan, dan maintainability.
