import re

# Exact regex from the implementation
_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

test_strings = [
    'a<b>:"/\\|?*c',
    'a<b>:"/|?*c',
]

for test in test_strings:
    print(f'Input: {test!r}')
    cleaned = _UNSAFE_FILENAME_CHARS.sub('_', test)
    print(f'  After unsafe char removal: {cleaned!r}')
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    print(f'  After space to underscore: {cleaned!r}')
    cleaned = re.sub(r'_{2,}', '_', cleaned)
    print(f'  After collapsing underscores: {cleaned!r}')
    cleaned = cleaned.strip('_. ')
    print(f'  After stripping: {cleaned!r}')
    print()