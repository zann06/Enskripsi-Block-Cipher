import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.padding import pad_pkcs7, unpad_pkcs7, PaddingError

# Test invalid padding
test_cases = [
    b"",                      # kosong tidak punya padding
    b"\x41",                  # panjang bukan kelipatan blok
    b"\x41\x42\x43",          # 3 byte, bukan kelipatan 2
    b"\x41\x00",              # nilai padding 0
    b"\x41\x03",              # nilai padding melebihi ukuran blok
    b"\x41\x02\x42\x01",      # byte padding tidak konsisten
    b"\x02\x01\x02\x01",      # pola inkonsisten lain
]

for i, data in enumerate(test_cases):
    try:
        result = unpad_pkcs7(data, 2)
        print(f'Test {i}: NO ERROR raised, unpad result: {result.hex()}')
    except PaddingError as e:
        print(f'Test {i}: PaddingError raised: {e}')
    except Exception as e:
        print(f'Test {i}: Other error raised: {type(e).__name__}: {e}')