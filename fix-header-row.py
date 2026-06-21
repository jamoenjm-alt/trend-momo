"""
fix-header-row.py — Column header row (TICKER/DESCRIPTION/etc) gets hidden
when filtering by section. Fix: don't tag <th> rows with data-section,
so they're never touched by applyFilter.
Run: python fix-header-row.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── Fix tagRows: skip rows that contain <th> elements ────────────────────────
OLD_TAG = "} else if (row.querySelectorAll('td, th').length > 1) {"
NEW_TAG = "} else if (row.querySelectorAll('td').length > 1 && !row.querySelector('th')) {"

if OLD_TAG in content:
    content = content.replace(OLD_TAG, NEW_TAG, 1)
    changes += 1
    print('✓  tagRows: <th> rows excluded from data-section tagging')
elif NEW_TAG in content:
    print('–  tagRows fix already applied')
else:
    print('✗  tagRows pattern not matched')
    idx = content.find("querySelectorAll('td, th')")
    if idx != -1: print(repr(content[idx-10:idx+60]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
