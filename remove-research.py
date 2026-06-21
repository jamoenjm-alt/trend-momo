"""remove-research.py — removes Research tab from topbar nav"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

OLD = "h('a', { href:'#' }, 'Watchlist'), h('a', { href:'#' }, 'Signals'), h('a', { href:'#' }, 'Research')"
NEW = "h('a', { href:'#' }, 'Watchlist'), h('a', { href:'#' }, 'Signals')"

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    shutil.copy2(path, 'index.html')
    print('✓  Research tab removed. Run: .\\git-push.bat')
elif NEW in content:
    print('–  Already removed.')
else:
    print('✗  Not matched.')
