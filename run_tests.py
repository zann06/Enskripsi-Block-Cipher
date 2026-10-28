import subprocess
import sys

# Run pytest and capture results
result = subprocess.run(
    [sys.executable, '-m', 'pytest', '-q', '--tb=short'],
    capture_output=True,
    text=True,
    cwd=r'C:\project\Kriptografi'
)

# Show ALL output
print("=== STDOUT ===")
print(result.stdout)
print("=== STDERR ===")
print(result.stderr)
print(f'\nReturn code: {result.returncode}')