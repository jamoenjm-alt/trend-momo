"""find-keys.py — shows all API key constants in the HTML. Paste output to Claude."""
import re
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

print("=== All key-like constants ===")
for m in re.finditer(r"const \w+\s*=\s*['\"][^'\"]{0,60}['\"]", content):
    line = m.group()
    if any(w in line.lower() for w in ['key', 'token', 'api', 'secret', 'auth', 'fh', 'av_', 'td_', 'finn']):
        print(line)
