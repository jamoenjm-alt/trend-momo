"""
fix-badges2.py — Fixes regime badge descriptions getting cut off.
Replaces the <table> in How to Use with divs, bypassing global table min-width CSS.
Run: python fix-badges2.py  then: .\\git-push.bat
"""
import sys, shutil

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Add CSS override targeting the specific table ─────────────────────────
# The global rule is: table { min-width: 900px; }
# We override with higher specificity + !important on our specific class
TABLE_OVERRIDE = """
    /* force How-to-Use regime table to respect its container */
    table.htu-reg-table { min-width: 0 !important; width: 100% !important; }"""

if 'table.htu-reg-table' not in content:
    content = content.replace('</style>', TABLE_OVERRIDE + '\n  </style>', 1)
    changes += 1
    print('✓  table.htu-reg-table CSS override added')
else:
    print('–  override already present')

# ── 2. Replace the <table> with a div-based layout (bulletproof fix) ─────────
OLD_TABLE = """          <table class="htu-reg-table">
            <tr><td><span class="htu-badge htu-sb">STRONG BULL</span></td><td>All signals bullish. Highest conviction uptrend.</td></tr>
            <tr><td><span class="htu-badge htu-wb">WEAK BULL</span></td><td>Mostly bullish. Trend up, moderate conviction.</td></tr>
            <tr><td><span class="htu-badge htu-sw">SIDEWAYS</span></td><td>Mixed signals. Choppy — wait for clarity.</td></tr>
            <tr><td><span class="htu-badge htu-wbr">WEAK BEAR</span></td><td>Mostly bearish. Reduce long exposure.</td></tr>
            <tr><td><span class="htu-badge htu-sbr">STRONG BEAR</span></td><td>All signals bearish. Exit longs.</td></tr>
          </table>"""

NEW_TABLE = """          <div class="htu-badge-list">
            <div class="htu-badge-row"><span class="htu-badge htu-sb">STRONG BULL</span><span>All signals bullish. Highest conviction uptrend.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-wb">WEAK BULL</span><span>Mostly bullish. Trend up, moderate conviction.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-sw">SIDEWAYS</span><span>Mixed signals. Choppy — wait for clarity.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-wbr">WEAK BEAR</span><span>Mostly bearish. Reduce long exposure.</span></div>
            <div class="htu-badge-row"><span class="htu-badge htu-sbr">STRONG BEAR</span><span>All signals bearish. Exit longs.</span></div>
          </div>"""

if OLD_TABLE in content:
    content = content.replace(OLD_TABLE, NEW_TABLE, 1)
    changes += 1
    print('✓  Regime badges: table → divs (bypasses global table CSS)')
elif 'htu-badge-list' in content:
    print('–  Already using div layout')
else:
    print('✗  Regime badges table not matched — showing context:')
    idx = content.find('htu-badge htu-sb')
    if idx != -1: print(repr(content[max(0,idx-80):idx+400]))

# ── 3. Add div-based badge layout CSS ────────────────────────────────────────
BADGE_LIST_CSS = """
    .htu-badge-list { margin-top: 6px; }
    .htu-badge-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 6px; font-size: 0.74rem; color: #374151; line-height: 1.4; }
    .htu-badge-row .htu-badge { flex-shrink: 0; margin-top: 1px; }"""

if '.htu-badge-list' not in content:
    content = content.replace('</style>', BADGE_LIST_CSS + '\n  </style>', 1)
    changes += 1
    print('✓  htu-badge-list CSS added')
else:
    print('–  htu-badge-list CSS already present')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Now run: .\\git-push.bat')
