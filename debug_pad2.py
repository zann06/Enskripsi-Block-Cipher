import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.padding import unpad_pkcs7, PaddingError

# Exact test cases from pytest parameterized test
test_data = [
    b"",                       # kosong tidak punya padding
    b"\x41",                   # panjang bukan kelipatan blok
    b"\x41\x42\x43",           # 3 byte, bukan kelipatan 2
    b"\x41\x00",               # nilai padding 0
    b"\x41\x03",               # nilai padding melebihi ukuran blok
    b"\x41\x02\x42\x01",       # byte padding tidak konsisten
    b"\x02\x01\x02\x01",       # pola inkonsisten lain
]

for i, data in enumerate(test_data):
    try:
        result = unpad_pkcs7(data)  # pakai default block_size=2
        print(f'Test {i}: NO ERROR - result={result.hex() if result else "None"}')
    except PaddingError as e:
        print(f'Test {i}: PaddingError - {e}')
    except Exception as e:
        print(f'Test {i}: {type(e).__name__} - {e}')