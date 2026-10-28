import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.cbc import encrypt_cbc
from crypto.feistel16 import BLOCK_BYTES, MAX_BLOCK
from crypto.padding import pad_pkcs7

plaintext = 'Halo dunia! Uji coba blok'.encode('utf-8')
KEY = 0x1A2B
IV = 0x0F0F

# Pad the plaintext
padded = pad_pkcs7(plaintext, BLOCK_BYTES)
print(f'Plaintext length: {len(plaintext)}')
print(f'Padded length: {len(padded)}')
print(f'Number of 2-byte blocks: {len(padded) // BLOCK_BYTES}')
print()

# Manual CBC encryption
ciphertext = b''
previous = IV.to_bytes(BLOCK_BYTES, 'big')
blocks_info = []

for i in range(len(padded) // BLOCK_BYTES):
    block_start = i * BLOCK_BYTES
    block_end = (i + 1) * BLOCK_BYTES
    plain_block = padded[block_start:block_end]
    
    # XOR with previous
    xored = bytes(a ^ b for a, b in zip(plain_block, previous))
    
    # Encrypt the XORed block
    from crypto.feistel16 import encrypt_block
    cipher_int, rounds = encrypt_block(int.from_bytes(xored, 'big'), KEY, collect_trace=True)
    cipher_block = int.to_bytes(cipher_int, BLOCK_BYTES, 'big')
    
    blocks_info.append({
        'plaintext_block': plain_block.hex(),
        'xored': xored.hex(),
        'ciphertext_block': cipher_block.hex(),
        'feistel_input': xored.hex(),  # This is what goes into Feistel
        'xor_value': previous.hex(),    # This is what's stored in BlockTrace.xor_value
    })
    
    ciphertext += cipher_block
    previous = cipher_block  # For next block

print('Manual CBC encryption:')
for i, info in enumerate(blocks_info):
    print(f'Block {i}:')
    print(f'  plaintext_block: {info["plaintext_block"]}')
    print(f'  xored (P XOR C_prev): {info["xored"]}')
    print(f'  ciphertext_block: {info["ciphertext_block"]}')
    print(f'  feistel_input (what goes to Feistel): {info["feistel_input"]}')
    print(f'  xor_value (stored in BlockTrace): {info["xor_value"]}')
    print()

# Now compare with actual implementation
print('=== Actual implementation ===')
ciphertext2, blocks = encrypt_cbc(plaintext, KEY, IV)
print(f'Ciphertext2 length: {len(ciphertext2)}, num blocks: {len(blocks)}')
for i, b in enumerate(blocks):
    print(f'Block {i}:')
    print(f'  plaintext_block: {b.plaintext_block.hex()}')
    print(f'  ciphertext_block: {b.ciphertext_block.hex()}')
    print(f'  feistel_input: {b.feistel_input.hex()}')
    print(f'  xor_value: {b.xor_value.hex() if b.xor_value else "None"}')
    print()