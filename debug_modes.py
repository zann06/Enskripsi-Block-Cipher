import sys
sys.path.insert(0, r'C:\project\Kriptografi')
from crypto.pipeline import execute_mode
from crypto.encoding import text_to_bytes, format_hex, format_bin

# Test ECB
print("=== ECB Mode ===")
result = execute_mode("ECB", "Halo dunia!", key=0x1A2B)
print(f"Mode: {result.mode}")
print(f"Verified: {result.verified}")
print(f"Ciphertext: {format_hex(result.ciphertext)}")
print(f"Decrypted: {result.decrypted_text}")
print(f"Blocks: {result.block_count}")
print()

# Test CBC
print("=== CBC Mode ===")
result = execute_mode("CBC", "Halo dunia!", key=0x1A2B, iv=0x0F0F)
print(f"Mode: {result.mode}")
print(f"Verified: {result.verified}")
print(f"Ciphertext: {format_hex(result.ciphertext)}")
print(f"Decrypted: {result.decrypted_text}")
print(f"Blocks: {result.block_count}")
print()

# Test CTR
print("=== CTR Mode ===")
result = execute_mode("CTR", "Halo Dunia!", key=0x1A2B, initial_counter=0x00C8)
print(f"Mode: {result.mode}")
print(f"Verified: {result.verified}")
print(f"Ciphertext: {format_hex(result.ciphertext)}")
print(f"Decrypted: {result.decrypted_text}")
print(f"Blocks: {result.block_count}")
print(f"Padding: {result.padding}")