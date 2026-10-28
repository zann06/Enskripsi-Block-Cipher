import re

# Read the README
with open(r'C:\project\Kriptografi\README.md', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find and replace the Catatan section using regex
pattern = r'### Catatan:.*?(?=## License)'
match = re.search(pattern, content, re.DOTALL)
if match:
    old_text = match.group()
    new_text = """### Catatan:
- Screenshot di atas menunjukkan antarmuka CipherLab yang sebenarnya saat dijalankan via `streamlit run app.py`
- Screenshot dapat di-capture saat aplikasi berjalan di browser di `http://localhost:8501`
- Aplikasi memiliki tema navy/vetitabu yang modern dan minimis
- Semua nilai yang ditampilkan berasal dari eksekusi aktual, bukan data dummy
- Mode yang belum dijalankan ditandai "Belum dijalankan" dengan jelas
- Gambar di atas digunakan sebagai referensi; screenshot aktual disimpan di `docs/screenshots/`"""

    content = content.replace(old_text, new_text)
    with open(r'C:\project\Kriptografi\README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replacement done successfully')
else:
    print('Regex match failed - could not find Catatan section')