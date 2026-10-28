import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.ctr import encrypt_ctr, CounterOverflowError
from crypto.encoding import text_to_bytes

# Test: counter overflow - use a small counter that will overflow
plaintext = text_to_bytes("A" * 100)  # 100 bytes, lots of blocks

try:
    ciphertext, blocks = encrypt_ctr(plaintext, key=0x1A2B, initial_counter=0xFFFF)
    print(f'No error raised. Ciphertext length: {len(ciphertext)}')
except CounterOverflowError as e:
    print(f'CounterOverflowError raised: {e}')
except Exception as e:
    print(f'{type(e).__name__} raised: {e}')