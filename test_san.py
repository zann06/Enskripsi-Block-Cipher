from reports import sanitize_filename
result = sanitize_filename('a<b>:|\"/\\\\|?*c')
print('Result:', result)
print('Expected: a_c')
print('Match:', result == 'a_c')