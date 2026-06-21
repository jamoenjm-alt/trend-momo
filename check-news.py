"""check-news.py — shows how the news key is actually used in code. Paste output to Claude."""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

# Find FH_KEY_DEFAULT usage
import re
idx = content.find('FH_KEY_DEFAULT')
print("=== FH_KEY_DEFAULT definition + nearby usage ===")
print(content[max(0,idx-100):idx+400])

# Find the news fetch function
print("\n=== fetchAVNews / fetchNews function ===")
for name in ['fetchAVNews', 'fetchNews', 'fetchFinnhub', 'NEWS']:
    idx2 = content.find(f'function {name}')
    if idx2 == -1: idx2 = content.find(f'const {name}')
    if idx2 != -1:
        print(f"Found '{name}' at {idx2}:")
        print(content[idx2:idx2+600])
        break

# Find where fhKey / FH_KEY is read from localStorage
print("\n=== localStorage fhKey reads ===")
for m in re.finditer(r'.{0,60}[Ff][Hh][Kk]ey.{0,80}', content):
    print(m.group())
