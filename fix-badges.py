"""
fix-badges.py — Fixes regime badge descriptions getting cut off in How to Use
Run: python fix-badges.py  then: .\\git-push.bat
"""
import sys, shutil

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Root cause: global table { min-width: 900px } makes .htu-reg-table 900px wide
# inside a ~220px grid column. overflow: hidden on .htu-block clips the description.
# Fix: force min-width: 0 on the table so it stays within its container.

OLD = '    .htu-reg-table { width: 100%; border-collapse: collapse; margin-top: 5px; table-layout: fixed; }'
NEW = '    .htu-reg-table { width: 100% !important; min-width: 0 !important; border-collapse: collapse; margin-top: 5px; table-layout: fixed; }'

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    changes += 1
    print('✓  htu-reg-table: min-width: 0 !important added')
elif 'min-width: 0 !important' in content[content.find('.htu-reg-table'):content.find('.htu-reg-table')+200]:
    print('–  htu-reg-table already has min-width fix')
else:
    print('✗  htu-reg-table CSS not matched:')
    idx = content.find('.htu-reg-table {')
    if idx != -1: print(repr(content[idx:idx+150]))

# Also fix first-column width so badge takes less horizontal room
OLD2 = '    .htu-reg-table td:first-child { width: 110px; }'
NEW2 = '    .htu-reg-table td:first-child { width: 100px; }'
if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    changes += 1
    print('✓  htu-reg-table badge column: 110→100px')
elif '    .htu-reg-table td:first-child { width: 120px; }' in content:
    content = content.replace(
        '    .htu-reg-table td:first-child { width: 120px; }',
        '    .htu-reg-table td:first-child { width: 100px; }', 1
    )
    changes += 1
    print('✓  htu-reg-table badge column: 120→100px')
else:
    print('–  badge column already updated or not found')

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Now run: .\\git-push.bat')
