"""set-api-keys.py — patches Finnhub key into HTML"""
import sys, shutil

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

OLD = "const FH_KEY_DEFAULT = ''"
NEW = "const FH_KEY_DEFAULT = 'd8rm9ghr01qnkitoq79gd8rm9ghr01qnkitoq7a0'"

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    shutil.copy2(path, 'index.html')
    print('✓  FH_KEY_DEFAULT set. Now run: .\\git-push.bat')
elif NEW in content:
    print('–  Key already set. Run: .\\git-push.bat')
else:
    print('✗  Not matched')
