import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.ecb import encrypt_ecb

# Test: identical blocks
plaintext = b'\x41\x42' * 4
ciphertext, blocks = encrypt_ecb(plaintext, 0x1A2B)
print('ECB blocks ciphertext hex:')
for b in blocks:
    print(f'  Block {b.index}: {b.ciphertext_block.hex()}')
unique = len(set(b.ciphertext_block for b in blocks))
print(f'Unique ciphertext blocks: {unique}')