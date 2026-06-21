"""
diagnose.py — Run this and paste ALL output back to Claude
"""
import os, subprocess, sys

print("=== CWD ===")
print(os.getcwd())
print()

print("=== regime-board.html path ===")
p = os.path.abspath('regime-board.html')
print(p)
print("Exists:", os.path.exists(p))
if os.path.exists(p):
    print("Size:", os.path.getsize(p), "bytes")
print()

print("=== git remote -v ===")
r = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
print(r.stdout or r.stderr)

print("=== git status ===")
r = subprocess.run(['git', 'status'], capture_output=True, text=True)
print(r.stdout or r.stderr)

print("=== git log --oneline -3 ===")
r = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
print(r.stdout or r.stderr)

print("=== git diff --stat HEAD ===")
r = subprocess.run(['git', 'diff', '--stat', 'HEAD'], capture_output=True, text=True)
print(r.stdout or r.stderr)

print("=== CSS probe (tooltip + dot-very-stable) ===")
try:
    with open('regime-board.html', encoding='utf-8') as f:
        html = f.read()
    # Tooltip width
    idx = html.find('.tooltip {')
    if idx != -1:
        print("Tooltip block:", repr(html[idx:idx+120]))
    else:
        print("ERROR: .tooltip { not found")
    # Dot colour
    idx2 = html.find('.dot-very-stable')
    if idx2 != -1:
        print("Dot CSS:", repr(html[idx2:idx2+80]))
    else:
        print("ERROR: .dot-very-stable not found")
    # tt-table
    idx3 = html.find('.tt-table {')
    if idx3 != -1:
        print("tt-table CSS:", repr(html[idx3:idx3+80]))
    else:
        print("ERROR: .tt-table { not found")
except Exception as e:
    print("Error reading file:", e)
