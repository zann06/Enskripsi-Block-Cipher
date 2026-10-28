import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.encoding import sanitize_filename

# Test cases from pytest
test_cases = [
    ("Kelompok 3", "Kelompok_3"),
    ('a<b":"/\\|?*c', "a_c"),  # This is the failing case
    ("  spasi  ganda  ", "spasi_ganda"),
    ("..", "Laporan_CipherLab"),
    ("", "Laporan_CipherLab"),
    ("___", "Laporan_CipherLab"),
    ("CON", "Laporan_CON"),
    ("report.pdf", "report.pdf"),
    ("Zo� �", "Zo�_�"),
    ("Kelompok 3: Laporan *Final* v2?", "Kelompok_3_Laporan_Final_v2"),
]

print("Testing sanitize_filename:")
for raw, expected in test_cases:
    result = sanitize_filename(raw)
    status = "PASS" if result == expected else "FAIL"
    print(f'  {status}: sanitize_filename({raw!r}) = {result!r} (expected {expected!r})')