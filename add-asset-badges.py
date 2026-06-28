"""
add-asset-badges.py — Adds asset type badges (Crypto/Equity/ASX/ETF/Forex/Cmdty/HK)
next to each ticker in the Reversal Watch and RSI Divergences panels.

Run: python add-asset-badges.py  then: .\\git-push.bat
"""
import sys, shutil

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

changes = 0

# ── 1. CSS ────────────────────────────────────────────────────────────────────
CSS = """
    /* ── Asset type badge (Reversal & Divergence panels) ──────── */
    .atbadge { display:inline-block; font-size:0.52rem; font-weight:800; letter-spacing:0.04em; padding:1px 4px; border-radius:3px; margin-left:4px; vertical-align:middle; line-height:1.4; }
    .atbadge-crypto  { background:#7c3aed; color:#ede9fe; }
    .atbadge-equity  { background:#1e40af; color:#dbeafe; }
    .atbadge-asx     { background:#065f46; color:#d1fae5; }
    .atbadge-etf     { background:#374151; color:#e5e7eb; }
    .atbadge-forex   { background:#92400e; color:#fef3c7; }
    .atbadge-cmdty   { background:#78350f; color:#fef3c7; }
    .atbadge-hk      { background:#9f1239; color:#ffe4e6; }"""

if '.atbadge' not in src:
    src = src.replace('</style>', CSS + '\n  </style>', 1)
    changes += 1
    print('✓ Asset badge CSS added')
else:
    print('– CSS already present')

# ── 2. TICKER_CLS_MAP + assetBadge() helper ───────────────────────────────────
HELPER = """
// ── Ticker → asset class lookup for badge display ───────────────────────────
const TICKER_CLS_MAP = {};
for (const a of WATCHLIST) { if (!TICKER_CLS_MAP[a.ticker]) TICKER_CLS_MAP[a.ticker] = a.cls; }
function assetBadge(ticker) {
  const cls = TICKER_CLS_MAP[ticker] || '';
  const labelMap = { Crypto:'Crypto', ASX:'ASX', Index:'ETF', Forex:'Forex', Commodity:'Cmdty', HK:'HK' };
  const label = labelMap[cls] || 'Equity';
  const cssMap = { Crypto:'crypto', ASX:'asx', ETF:'etf', Forex:'forex', Cmdty:'cmdty', HK:'hk', Equity:'equity' };
  return h('span', { className: 'atbadge atbadge-' + cssMap[label] }, label);
}

"""

INJECT_BEFORE = '// ── Signal maths ──────────────────────────────────────────────'
ALT_INJECT_BEFORE = '// ── Signal maths'

if 'assetBadge' not in src:
    if INJECT_BEFORE in src:
        src = src.replace(INJECT_BEFORE, HELPER + INJECT_BEFORE, 1)
        changes += 1
        print('✓ TICKER_CLS_MAP + assetBadge() added')
    elif ALT_INJECT_BEFORE in src:
        src = src.replace(ALT_INJECT_BEFORE, HELPER + ALT_INJECT_BEFORE, 1)
        changes += 1
        print('✓ TICKER_CLS_MAP + assetBadge() added (alt injection)')
    else:
        # Find a safe spot — before MA_PAIRS
        fallback = 'const MA_PAIRS = ['
        if fallback in src:
            src = src.replace(fallback, HELPER + fallback, 1)
            changes += 1
            print('✓ TICKER_CLS_MAP + assetBadge() added (MA_PAIRS fallback)')
        else:
            print('✗ Could not find injection point for assetBadge helper')
else:
    print('– assetBadge already present')

# ── 3. ReversalWatch makeRow — add asset badge after ticker ───────────────────
OLD_REV_ROW = """  const makeRow = (r) => h('div', { key: r.ticker, className: 'reversal-row' },
    h('span', { className: 'reversal-ticker' }, r.ticker),
    h('span', { className: 'reversal-arrow' }, r.prevLabel + ' → ' + r.nowLabel),
    h('span', { className: 'reversal-strength ' + r.strCls }, r.strength),
  );"""

NEW_REV_ROW = """  const makeRow = (r) => h('div', { key: r.ticker, className: 'reversal-row' },
    h('span', { className: 'reversal-ticker' }, r.ticker, assetBadge(r.ticker)),
    h('span', { className: 'reversal-arrow' }, r.prevLabel + ' → ' + r.nowLabel),
    h('span', { className: 'reversal-strength ' + r.strCls }, r.strength),
  );"""

if OLD_REV_ROW in src:
    src = src.replace(OLD_REV_ROW, NEW_REV_ROW, 1)
    changes += 1
    print('✓ ReversalWatch makeRow updated')
elif 'assetBadge(r.ticker)' in src:
    print('– ReversalWatch already patched')
else:
    print('✗ ReversalWatch makeRow not found — check string match')
    idx = src.find('const makeRow = (r)')
    if idx != -1: print(repr(src[idx:idx+200]))

# ── 4. DivergenceWatch row — add asset badge after ticker ─────────────────────
OLD_DIV_ROW = """  const row = (d) => h('div', { key: d.ticker + d.tf, className: 'reversal-row' },
    h('span', { className: 'reversal-ticker' }, d.ticker),
    h('span', { className: 'reversal-arrow' }, h('span', { className: 'div-tf div-tf-' + d.tf.toLowerCase() }, d.tf), ' RSI div'),
    h('span', { className: 'reversal-strength ' + sCls(d.strength) }, sLbl(d.strength)),
  );"""

NEW_DIV_ROW = """  const row = (d) => h('div', { key: d.ticker + d.tf, className: 'reversal-row' },
    h('span', { className: 'reversal-ticker' }, d.ticker, assetBadge(d.ticker)),
    h('span', { className: 'reversal-arrow' }, h('span', { className: 'div-tf div-tf-' + d.tf.toLowerCase() }, d.tf), ' RSI div'),
    h('span', { className: 'reversal-strength ' + sCls(d.strength) }, sLbl(d.strength)),
  );"""

if OLD_DIV_ROW in src:
    src = src.replace(OLD_DIV_ROW, NEW_DIV_ROW, 1)
    changes += 1
    print('✓ DivergenceWatch row updated')
elif 'assetBadge(d.ticker)' in src:
    print('– DivergenceWatch already patched')
else:
    print('✗ DivergenceWatch row not found — check string match')
    idx = src.find('const row = (d)')
    if idx != -1: print(repr(src[idx:idx+200]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy2(path, 'index.html')
print(f'\n✓ {changes} change(s) applied. index.html synced. Run: .\\git-push.bat')
