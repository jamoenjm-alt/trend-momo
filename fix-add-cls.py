"""
fix-add-cls.py — Patches the doAdd push to store active section cls.
Targets the simple push line that fix-custom-add.py already injected.
Run: python fix-add-cls.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Find the exact push line left by fix-custom-add.py
OLD_PUSH = "      list.push({ ticker: ticker, name: ticker });\n      saveCustomTickers(list);\n      location.reload();"
NEW_PUSH = """      var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
      list.push({ ticker: ticker, name: ticker, cls: activeCls });
      saveCustomTickers(list);
      location.reload();"""

if OLD_PUSH in content:
    content = content.replace(OLD_PUSH, NEW_PUSH, 1)
    changes += 1
    print('✓  doAdd now stores cls from active section filter')
elif 'activeCls' in content:
    print('–  activeCls already in doAdd')
else:
    print('✗  push line not matched')
    idx = content.find('list.push({ ticker: ticker, name: ticker')
    if idx != -1: print(repr(content[idx-5:idx+80]))

# Also check "Top 20 US" remnant — find and report where it is
count = content.count("'Top 20 US'") + content.count('"Top 20 US"') + content.count('>Top 20 US<')
if count:
    print(f'ℹ  "Top 20 US" still appears {count}x (likely in nav button HTML — harmless if not visible)')

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
