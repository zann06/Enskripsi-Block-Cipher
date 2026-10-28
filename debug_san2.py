import re

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

test = 'a<b>:"/\\|?*c'
matches = _UNSAFE_FILENAME_CHARS.findall(test)
print(f'String: {test!r}')
print(f'Matches: {matches!r}')
print(f'Match positions: {[test.index(m) if m in test else "?" for m in matches]}')

# Also check each character
for i, c in enumerate(test):
    code = ord(c)
    in_range = 0x00 <= code <= 0x1f
    explicit_chars = c in '<>:/\\|?*'
    print(f'  {c!r} (0x{code:02X}): explicit={explicit_chars}, in_0x00_1f={in_range}')