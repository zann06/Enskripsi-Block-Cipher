import subprocess
import sys

# Initialize git repo
result = subprocess.run(['git', 'init'], capture_output=True, text=True, cwd=r'C:\project\Kriptografi')
print('=== git init ===')
print('stdout:', result.stdout)
print('stderr:', result.stderr)

# Add all files
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True, cwd=r'C:\project\Kriptografi')
print('=== git add -A ===')
print('stdout:', result.stdout)
print('stderr:', result.stderr)

# Create initial commit
result = subprocess.run(['git', 'commit', '-m', 'Initial CipherLab commit'], capture_output=True, text=True, cwd=r'C:\project\Kriptografi')
print('=== git commit ===')
print('stdout:', result.stdout)
print('stderr:', result.stderr)

# Check status
result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd=r'C:\project\Kriptografi')
print('=== git status ===')
print('stdout:', result.stdout)
print('stderr:', result.stderr)