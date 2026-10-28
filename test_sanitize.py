from reports import sanitize_filename

test_cases = [
    ('Kelompok 3', 'Kelompok_3'),
    ('a<b>:"/\\|?*c', 'a_c'),
    ('  spasi  ganda  ', 'spasi_ganda'),
    ('..', 'Laporan_CipherLab'),
    ('', 'Laporan_CipherLab'),
    ('___', 'Laporan_CipherLab'),
    ('CON', 'Laporan_CON'),
    ('report.pdf', 'report.pdf'),
]

for raw, expected in test_cases:
    result = sanitize_filename(raw)
    status = 'OK' if result == expected else 'FAIL'
    print(f'{status}: sanitize_filename({raw!r}) = {result!r} (expected {expected!r})')