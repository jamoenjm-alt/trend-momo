"""
fix-tooltip-size.py — Makes tooltip ~half size, cleaner and easier on the eyes
Run: python fix-tooltip-size.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Tooltip CSS width 380 → 240px ─────────────────────────────────────────
if 'width: 380px;' in content:
    content = content.replace('width: 380px;', 'width: 240px;', 1)
    changes += 1
    print('✓  Tooltip CSS width: 380→240px')
elif 'width: 240px;' in content:
    print('–  Already 240px')
else:
    print('✗  Tooltip width not found')

# ── 2. panelW 380 → 240 ──────────────────────────────────────────────────────
if 'const panelW = 380;' in content:
    content = content.replace('const panelW = 380;', 'const panelW = 240;', 1)
    changes += 1
    print('✓  panelW: 380→240')
elif 'const panelW = 240;' in content:
    print('–  panelW already 240')
else:
    print('✗  panelW not found')

# ── 3. Smaller group section labels ──────────────────────────────────────────
OLD_GROUP_LABEL = ("h('div', { style: { fontSize: '0.55rem', fontWeight: 800, "
                   "letterSpacing: '0.1em', color: '#475569', textTransform: 'uppercase', marginBottom: 4 } }, GROUP_LABEL[g])")
NEW_GROUP_LABEL = ("h('div', { style: { fontSize: '0.5rem', fontWeight: 700, "
                   "letterSpacing: '0.08em', color: '#4b5563', textTransform: 'uppercase', marginBottom: 2 } }, GROUP_LABEL[g])")
if OLD_GROUP_LABEL in content:
    content = content.replace(OLD_GROUP_LABEL, NEW_GROUP_LABEL, 1)
    changes += 1
    print('✓  Group labels: smaller')
else:
    print('–  Group label style not matched (skipping)')

# ── 4. Smaller pill badges (padding + font) ───────────────────────────────────
OLD_PILL_STYLE = "display: 'inline-block', minWidth: 28, padding: '2px 6px', borderRadius: '4px', fontWeight: 800, fontSize: '0.62rem'"
NEW_PILL_STYLE = "display: 'inline-block', minWidth: 22, padding: '1px 4px', borderRadius: '3px', fontWeight: 700, fontSize: '0.56rem'"
if OLD_PILL_STYLE in content:
    content = content.replace(OLD_PILL_STYLE, NEW_PILL_STYLE)  # replace all occurrences (trend + momo)
    changes += 1
    print('✓  Pill badges: smaller')
else:
    print('–  Pill style not matched (skipping)')

# ── 5. Tighter row padding ────────────────────────────────────────────────────
OLD_ROW_PAD = "style: { textAlign: 'center', padding: '2px 1px' }"
NEW_ROW_PAD = "style: { textAlign: 'center', padding: '1px 0' }"
if OLD_ROW_PAD in content:
    content = content.replace(OLD_ROW_PAD, NEW_ROW_PAD)
    changes += 1
    print('✓  Row padding: tighter')
else:
    print('–  Row padding not matched (skipping)')

# ── 6. Smaller pair label font ────────────────────────────────────────────────
OLD_PAIR_FONT = "fontSize: '0.68rem', color: '#94a3b8', fontWeight: 700"
NEW_PAIR_FONT = "fontSize: '0.6rem', color: '#94a3b8', fontWeight: 600"
if OLD_PAIR_FONT in content:
    content = content.replace(OLD_PAIR_FONT, NEW_PAIR_FONT, 1)
    changes += 1
    print('✓  Pair label: smaller font')
else:
    print('–  Pair font not matched (skipping)')

# ── 7. Smaller % column font ──────────────────────────────────────────────────
OLD_PCT_FONT = "fontSize: '0.68rem', fontWeight: 700, color: p==null"
NEW_PCT_FONT = "fontSize: '0.6rem', fontWeight: 600, color: p==null"
if OLD_PCT_FONT in content:
    content = content.replace(OLD_PCT_FONT, NEW_PCT_FONT, 1)
    changes += 1
    print('✓  % column: smaller font')
else:
    print('–  % font not matched (skipping)')

# ── 8. Tighter group margin ───────────────────────────────────────────────────
OLD_GROUP_MARGIN = "style: { marginBottom: 9 }"
NEW_GROUP_MARGIN = "style: { marginBottom: 5 }"
if OLD_GROUP_MARGIN in content:
    content = content.replace(OLD_GROUP_MARGIN, NEW_GROUP_MARGIN)
    changes += 1
    print('✓  Group margin: tighter')
else:
    print('–  Group margin not matched (skipping)')

# ── 9. Tighter "Last:" price line ────────────────────────────────────────────
OLD_LAST = "fontSize: '0.65rem', color: '#94a3b8', marginBottom: 7, paddingBottom: 6, borderBottom: '1px solid #374151'"
NEW_LAST = "fontSize: '0.6rem', color: '#94a3b8', marginBottom: 5, paddingBottom: 4, borderBottom: '1px solid #2d3748'"
if OLD_LAST in content:
    content = content.replace(OLD_LAST, NEW_LAST, 1)
    changes += 1
    print('✓  Last price line: tighter')
else:
    print('–  Last line not matched (skipping)')

# ── 10. Update tt-table column widths for 240px ──────────────────────────────
OLD_COL1 = '    .tt-table th:nth-child(1), .tt-table td:nth-child(1) { width: 22%; }'
NEW_COL1 = '    .tt-table th:nth-child(1), .tt-table td:nth-child(1) { width: 26%; }'
OLD_COL2 = '    .tt-table th:nth-child(2), .tt-table td:nth-child(2) { width: 24%; }'
NEW_COL2 = '    .tt-table th:nth-child(2), .tt-table td:nth-child(2) { width: 22%; }'
OLD_COL3 = '    .tt-table th:nth-child(3), .tt-table td:nth-child(3) { width: 24%; }'
NEW_COL3 = '    .tt-table th:nth-child(3), .tt-table td:nth-child(3) { width: 22%; }'
OLD_COL4 = '    .tt-table th:nth-child(4), .tt-table td:nth-child(4) { width: 30%; }'
NEW_COL4 = '    .tt-table th:nth-child(4), .tt-table td:nth-child(4) { width: 30%; }'

for old, new in [(OLD_COL1,NEW_COL1),(OLD_COL2,NEW_COL2),(OLD_COL3,NEW_COL3)]:
    if old in content:
        content = content.replace(old, new, 1)
        changes += 1

print('✓  tt-table column widths adjusted for 240px')

# ── 11. Tooltip header font size ─────────────────────────────────────────────
OLD_TICKER = "className: 'tt-ticker'"
# Add a style override via CSS injection
TOOLTIP_COMPACT_CSS = """
    /* compact tooltip */
    .tt-header { font-size: 0.6rem !important; padding: 5px 8px !important; }
    .tt-ticker { font-size: 0.65rem !important; padding: 3px 8px 4px !important; }
    .tooltip { padding-bottom: 6px !important; }"""

if '.compact tooltip' not in content and 'compact tooltip' not in content:
    content = content.replace('</style>', TOOLTIP_COMPACT_CSS + '\n  </style>', 1)
    changes += 1
    print('✓  Compact tooltip CSS injected')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced.')
print('Run: .\\git-push.bat')
