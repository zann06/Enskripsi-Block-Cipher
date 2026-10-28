from crypto.pipeline import execute_mode
from reports import build_pdf_bytes, ReportMetadata, Member

# Execute modes
r_ecb = execute_mode('ECB', 'Halo dunia!', 0x1A2B)
r_cbc = execute_mode('CBC', 'Halo dunia!', 0x1A2B, iv=0x0F0F)
r_ctr = execute_mode('CTR', 'Halo dunia!', 0x1A2B, initial_counter=0x00C8)

# Create metadata
metadata = ReportMetadata(
    title='Laporan Praktikum Block Cipher',
    group_name='Kelompok 1',
    course='Kriptografi Dasar',
    lecturer='Dosen A',
    class_name='SI-42-01',
    members=[Member(name='Andi', nim='12345'), Member(name='Budi')],
    report_date='28 Oktober 2026',
    filename=''
)

# Build PDF
pdf_bytes = build_pdf_bytes(metadata, {'ECB': r_ecb, 'CBC': r_cbc, 'CTR': r_ctr})
print(f'PDF generated: {len(pdf_bytes)} bytes')

# Verify content
text = pdf_bytes.decode('latin-1', errors='replace')
checks = ['Laporan Praktikum', 'Kelompok 1', 'ECB', 'CBC', 'CTR', 'BERHASIL', 'GAGAL', 'Belum dijalankan']
for check in checks:
    found = check in text
    print(f'  "{check}": {"OK" if found else "MISSING"}')