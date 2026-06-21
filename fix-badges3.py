"""
fix-badges3.py — Stacks badge above description (no more cut-off regardless of column width)
Run: python fix-badges3.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Change badge rows to vertical layout ───────────────────────────────────
OLD_ROW_CSS = ('    .htu-badge-row { display: flex; align-items: flex-start; gap: 10px; '
               'margin-bottom: 6px; font-size: 0.74rem; color: #374151; line-height: 1.4; }')
NEW_ROW_CSS = ('    .htu-badge-row { display: flex; flex-direction: column; gap: 3px; '
               'margin-bottom: 9px; font-size: 0.74rem; color: #374151; line-height: 1.5; }')

if OLD_ROW_CSS in content:
    content = content.replace(OLD_ROW_CSS, NEW_ROW_CSS, 1)
    changes += 1
    print('✓  .htu-badge-row: side-by-side → stacked')
elif 'flex-direction: column' in content and '.htu-badge-row' in content:
    print('–  Already stacked')
else:
    print('✗  .htu-badge-row CSS not matched:')
    idx = content.find('.htu-badge-row {')
    if idx != -1: print(repr(content[idx:idx+150]))

# ── 2. Remove flex-shrink:0 from badge inside row (not needed for column layout)
OLD_BADGE_SHRINK = '    .htu-badge-row .htu-badge { flex-shrink: 0; margin-top: 1px; }'
NEW_BADGE_SHRINK = '    .htu-badge-row .htu-badge { align-self: flex-start; }'
if OLD_BADGE_SHRINK in content:
    content = content.replace(OLD_BADGE_SHRINK, NEW_BADGE_SHRINK, 1)
    changes += 1
    print('✓  Badge alignment updated for column layout')
elif 'align-self: flex-start' in content:
    print('–  Badge alignment already updated')
else:
    # Non-critical, skip silently
    pass

# ── 3. If table is still there (div replacement failed), force it to work ─────
if '<table class="htu-reg-table">' in content:
    # Nuke the whole table and replace with divs
    import re
    OLD_TABLE_RE = r'<table class="htu-reg-table">.*?</table>'
    NEW_TABLE_DIV = '''<div class="htu-badge-list">
            <div class="htu-badge-row"><span class="htu-badge htu-sb">STRONG BULL</span><span>All signals bullish. Highest conviction uptrend.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-wb">WEAK BULL</span><span>Mostly bullish. Trend up, moderate conviction.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-sw">SIDEWAYS</span><span>Mixed signals. Choppy — wait for clarity.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-wbr">WEAK BEAR</span><span>Mostly bearish. Reduce long exposure.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-sbr">STRONG BEAR</span><span>All signals bearish. Exit longs.</span></div>
          </div>'''
    new_content, n = re.subn(OLD_TABLE_RE, NEW_TABLE_DIV, content, count=1, flags=re.DOTALL)
    if n:
        content = new_content
        changes += 1
        print('✓  Regime badges: table replaced with divs (regex fallback)')
    else:
        print('✗  Table regex also failed')
elif 'htu-badge-list' in content:
    print('–  Div layout already in place')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed — paste ✗ lines back to Claude.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Now run: .\\git-push.bat')
