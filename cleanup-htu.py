"""
cleanup-htu.py — Fixes How to Use layout + adds light red stability dot
Run: python cleanup-htu.py  then: .\\git-push.bat
"""
import sys, shutil

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Fix htu-block overflow (CSS grid cells need min-width:0 to stay in lane)
OLD1 = '    .htu-block { font-size: 0.77rem; line-height: 1.65; color: #374151; }'
NEW1 = '    .htu-block { font-size: 0.77rem; line-height: 1.65; color: #374151; min-width: 0; overflow: hidden; }'
if OLD1 in content:
    content = content.replace(OLD1, NEW1, 1)
    changes += 1
    print('✓  htu-block: min-width: 0 added')
elif 'min-width: 0' in content[content.find('.htu-block {'):content.find('.htu-block {')+150]:
    print('–  htu-block already fixed')
else:
    print('✗  htu-block CSS not matched:')
    idx = content.find('.htu-block {')
    if idx != -1: print(repr(content[idx:idx+120]))

# ── 2. Fix htu-reg-table (regime badges table) ─────────────────────────────
OLD2 = '    .htu-reg-table { width: 100%; border-collapse: collapse; margin-top: 5px; }'
NEW2 = '    .htu-reg-table { width: 100%; border-collapse: collapse; margin-top: 5px; table-layout: fixed; }'
if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    changes += 1
    print('✓  htu-reg-table: table-layout: fixed added')
elif 'table-layout: fixed' in content[content.find('.htu-reg-table {'):content.find('.htu-reg-table {')+150]:
    print('–  htu-reg-table already fixed')
else:
    print('✗  htu-reg-table CSS not matched:')
    idx = content.find('.htu-reg-table {')
    if idx != -1: print(repr(content[idx:idx+120]))

# ── 3. Tighten htu-grid column min-width 270→220 ───────────────────────────
if 'minmax(270px, 1fr)' in content:
    content = content.replace('minmax(270px, 1fr)', 'minmax(220px, 1fr)', 1)
    changes += 1
    print('✓  htu-grid: column min-width 270→220px')
elif 'minmax(220px' in content:
    print('–  htu-grid already at 220px')
else:
    print('✗  htu-grid minmax not found')

# ── 4. Fix htu-reg-table first column width ────────────────────────────────
OLD4 = '    .htu-reg-table td:first-child { width: 120px; }'
NEW4 = '    .htu-reg-table td:first-child { width: 110px; }'
if OLD4 in content:
    content = content.replace(OLD4, NEW4, 1)
    changes += 1
    print('✓  htu-reg-table td width: 120→110px')
elif '110px' in content:
    print('–  htu-reg-table td already 110px')
else:
    print('✗  htu-reg-table td not matched')

# ── 5. Clean up htu-block heading spacing ──────────────────────────────────
OLD5 = '    .htu-block h3 { font-size: 0.68rem; font-weight: 700; color: #1e3a8a; margin-bottom: 7px; letter-spacing: 0.07em; text-transform: uppercase; border-bottom: 1px solid #dde5f0; padding-bottom: 4px; }'
NEW5 = '    .htu-block h3 { font-size: 0.65rem; font-weight: 800; color: #1e3a8a; margin: 0 0 8px; letter-spacing: 0.07em; text-transform: uppercase; border-bottom: 1px solid #dde5f0; padding-bottom: 5px; }'
if OLD5 in content:
    content = content.replace(OLD5, NEW5, 1)
    changes += 1
    print('✓  htu-block h3: spacing cleaned up')
else:
    print('–  htu-block h3 not matched (may already be updated)')

# ── 6. Add light red dot CSS before </style> ───────────────────────────────
LIGHT_RED_CSS = """
    /* ── light red (unstable-red) — 5th stability dot state ── */
    .dot-unstable-red { background: #fca5a5; border: 1px solid #f87171; }
    .sp-dot-lr        { background: #fca5a5; border: 1px solid #f87171; }
    .htu-dot-lr       { background: #fca5a5; border: 1px solid #f87171; }"""

if '.dot-unstable-red' not in content:
    content = content.replace('</style>', LIGHT_RED_CSS + '\n  </style>', 1)
    changes += 1
    print('✓  Light red dot CSS added')
else:
    print('–  Light red dot CSS already present')

# ── 7. Add light red dot to How to Use guide ───────────────────────────────
OLD_DOTS = ('          <div class="htu-dot-row"><span class="htu-sdot htu-dot-u"></span>'
            '<span><strong>Yellow</strong> — Changed recently. Watch closely.</span></div>\n'
            '          <div class="htu-dot-row"><span class="htu-sdot htu-dot-vu"></span>'
            '<span><strong>Red</strong> — Multiple flips in 30 days. Choppy — avoid trading.</span></div>')

NEW_DOTS = ('          <div class="htu-dot-row"><span class="htu-sdot htu-dot-u"></span>'
            '<span><strong>Yellow</strong> — Changed recently. Watch closely.</span></div>\n'
            '          <div class="htu-dot-row"><span class="htu-sdot htu-dot-lr"></span>'
            '<span><strong>Light red</strong> — High flip rate. Reduce exposure, tighten stops.</span></div>\n'
            '          <div class="htu-dot-row"><span class="htu-sdot htu-dot-vu"></span>'
            '<span><strong>Red</strong> — Multiple flips in 30 days. Choppy — avoid trading.</span></div>')

if OLD_DOTS in content:
    content = content.replace(OLD_DOTS, NEW_DOTS, 1)
    changes += 1
    print('✓  Light red dot added to How to Use guide')
elif 'htu-dot-lr' in content:
    print('–  Light red dot already in How to Use guide')
else:
    print('✗  How to Use dots not matched — showing context:')
    idx = content.find('htu-dot-u')
    if idx != -1: print(repr(content[max(0,idx-80):idx+300]))

# ── 8. Try to patch computeStabilityState to return 5 states ───────────────
# Multiple guesses from most to least likely code pattern
STABILITY_PATCHES = [
    (   # if/else chain with 2-space indent
        "  if (changes === 2) return 'unstable';\n  return 'very-unstable';",
        "  if (changes === 2) return 'unstable';\n  if (changes === 3) return 'unstable-red';\n  return 'very-unstable';"
    ),
    (   # if/else chain with 4-space indent
        "    if (changes === 2) return 'unstable';\n    return 'very-unstable';",
        "    if (changes === 2) return 'unstable';\n    if (changes === 3) return 'unstable-red';\n    return 'very-unstable';"
    ),
    (   # count-based >= comparisons
        "  if (same >= 2) return 'unstable';\n  return 'very-unstable';",
        "  if (same >= 2) return 'unstable';\n  if (same >= 1) return 'unstable-red';\n  return 'very-unstable';"
    ),
    (   # changes > threshold pattern
        "> 2) return 'very-unstable'",
        "> 3) return 'very-unstable';\n  if (changes > 2) return 'unstable-red'"
    ),
]

stability_patched = False
for old_s, new_s in STABILITY_PATCHES:
    if old_s in content:
        content = content.replace(old_s, new_s, 1)
        changes += 1
        print('✓  computeStabilityState: unstable-red 5th state added')
        stability_patched = True
        break

if not stability_patched:
    if 'unstable-red' in content:
        print('–  computeStabilityState already has unstable-red')
    else:
        print('✗  computeStabilityState: no pattern matched — paste context below to Claude:')
        idx = content.find("'very-unstable'")
        if idx != -1: print(repr(content[max(0,idx-300):idx+60]))
        else: print('   (very-unstable not found in content either)')

# ── 9. Try to patch StabilityDot component ─────────────────────────────────
SD_PATCHES = [
    (
        "'very-unstable': 'dot-very-unstable'",
        "'unstable-red': 'dot-unstable-red', 'very-unstable': 'dot-very-unstable'"
    ),
    (
        "unstable: 'dot-unstable',\n    'very-unstable': 'dot-very-unstable'",
        "unstable: 'dot-unstable',\n    'unstable-red': 'dot-unstable-red',\n    'very-unstable': 'dot-very-unstable'"
    ),
    (
        "? 'dot-unstable' : 'dot-very-unstable'",
        "? 'dot-unstable' : s === 'unstable-red' ? 'dot-unstable-red' : 'dot-very-unstable'"
    ),
]

sd_patched = False
for old_s, new_s in SD_PATCHES:
    if old_s in content:
        content = content.replace(old_s, new_s, 1)
        changes += 1
        print('✓  StabilityDot: unstable-red case wired up')
        sd_patched = True
        break

if not sd_patched:
    if 'unstable-red' in content and 'dot-unstable-red' in content:
        print('–  StabilityDot already handles unstable-red')
    else:
        print('✗  StabilityDot: no pattern matched — paste context below to Claude:')
        idx = content.find('dot-very-unstable')
        if idx != -1: print(repr(content[max(0,idx-250):idx+60]))

# ── 10. Rename "Coal Mine Canary" → "1-2 Week" in How to Use guide ─────────
for old_label in [
    '<strong>Coal Mine Canary</strong> — Earliest warning (3/10 &amp; 5/15 day MAs). Turns first. Expect false alarms.',
    '<strong>Coal Mine Canary</strong> — Earliest warning (3/10 & 5/15 day MAs). Turns first. Expect false alarms.',
]:
    if old_label in content:
        content = content.replace(
            old_label,
            '<strong>1–2 Week (Canary)</strong> — Earliest warning (3/10 &amp; 5/15 day MAs). Turns first. Expect false alarms.',
            1
        )
        changes += 1
        print('✓  "Coal Mine Canary" renamed to "1-2 Week (Canary)" in How to Use')
        break
else:
    if '1–2 Week (Canary)' in content:
        print('–  Canary already renamed')
    else:
        print('✗  Coal Mine Canary label not matched — showing context:')
        idx = content.find('Coal Mine')
        if idx != -1: print(repr(content[max(0,idx-30):idx+120]))

# ── Result ──────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed — paste all ✗ lines back to Claude.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Now run: .\\git-push.bat')
