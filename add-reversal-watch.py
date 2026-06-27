"""
add-reversal-watch.py  —  Adds a "Reversal Watch" panel next to Market Outlook.

Shows tickers whose composite signal score (allInd) shifted by ≥ 0.3
over the last 14 days, sorted by signal strength. Bullish turns on left,
bearish on right. Signals at a glance — potential reversals before they're obvious.

Run: python add-reversal-watch.py  then: .\\git-push.bat
"""
import shutil, sys, re

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. CSS ────────────────────────────────────────────────────────────────────
CSS = """
    /* ── Reversal Watch panel ─────────────────────────────────── */
    .reversal-wrap {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 18px;
    }
    .reversal-col {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
      min-height: 80px;
    }
    .reversal-col-bull { border-left: 3px solid #22c55e; }
    .reversal-col-bear { border-left: 3px solid #ef4444; }
    .reversal-col-title {
      font-size: 0.65rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .reversal-col-bull .reversal-col-title { color: #22c55e; }
    .reversal-col-bear .reversal-col-title { color: #ef4444; }
    .reversal-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 4px 0;
      border-bottom: 1px solid var(--border);
      gap: 8px;
    }
    .reversal-row:last-child { border-bottom: none; }
    .reversal-ticker {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text);
      min-width: 44px;
    }
    .reversal-arrow {
      font-size: 0.62rem;
      color: #64748b;
      flex: 1;
    }
    .reversal-strength {
      font-size: 0.58rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      padding: 2px 5px;
      border-radius: 3px;
    }
    .rev-strong  { background: #166534; color: #bbf7d0; }
    .rev-building{ background: #1e3a5f; color: #93c5fd; }
    .rev-emerging{ background: #292524; color: #a8a29e; }
    .reversal-empty {
      font-size: 0.65rem;
      color: #475569;
      padding: 6px 0;
    }"""

if '.reversal-wrap' not in content:
    content = content.replace('</style>', CSS + '\n  </style>', 1)
    changes += 1
    print('✓  Reversal Watch CSS added')
else:
    print('–  CSS already present')

# ── 2. computeReversals function (inject after computeStabilityState) ─────────
REVERSAL_FN = """
// ── Reversal Watch: detect 14-day signal regime shifts ──────────────────────
function computeReversals(data) {
  const LOOKBACK = 14;
  const MIN_DELTA = 0.3;
  const results = [];
  for (const a of WATCHLIST) {
    const closes = data[a.ticker + '__' + a.cls]?.closes;
    if (!closes || closes.length < LOOKBACK + 30) continue;
    const nowSigs  = computeSignals(closes);
    const prevSigs = computeSignals(closes.slice(0, closes.length - LOOKBACK));
    if (!nowSigs || !prevSigs) continue;
    const nowScore  = nowSigs.allInd;
    const prevScore = prevSigs.allInd;
    if (nowScore == null || prevScore == null) continue;
    const delta = nowScore - prevScore;
    if (Math.abs(delta) < MIN_DELTA) continue;
    const prevRegime = scoreToRegime(prevScore);
    const nowRegime  = scoreToRegime(nowScore);
    // Only flag if regime label actually changed
    if (prevRegime.key === nowRegime.key) continue;
    const absDelta = Math.abs(delta);
    const strength = absDelta >= 0.65 ? 'Strong' : absDelta >= 0.45 ? 'Building' : 'Emerging';
    const strCls   = absDelta >= 0.65 ? 'rev-strong' : absDelta >= 0.45 ? 'rev-building' : 'rev-emerging';
    results.push({
      ticker: a.ticker,
      name: a.name,
      prevLabel: prevRegime.label,
      nowLabel:  nowRegime.label,
      delta,
      strength,
      strCls,
      direction: delta > 0 ? 'bull' : 'bear',
    });
  }
  results.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  return results;
}

"""

INJECT_AFTER = '// ── Data fetchers ──────────────────────────────────────────────'

if 'computeReversals' not in content:
    if INJECT_AFTER in content:
        content = content.replace(INJECT_AFTER, REVERSAL_FN + INJECT_AFTER, 1)
        changes += 1
        print('✓  computeReversals() function added')
    else:
        print('✗  Injection point not found')
else:
    print('–  computeReversals already present')

# ── 3. ReversalWatch React component ─────────────────────────────────────────
REVERSAL_COMPONENT = """
function ReversalWatch({ data }) {
  const reversals = computeReversals(data);
  const bulls = reversals.filter(r => r.direction === 'bull').slice(0, 6);
  const bears = reversals.filter(r => r.direction === 'bear').slice(0, 6);
  const makeRow = (r) => h('div', { key: r.ticker, className: 'reversal-row' },
    h('span', { className: 'reversal-ticker' }, r.ticker),
    h('span', { className: 'reversal-arrow' }, r.prevLabel + ' → ' + r.nowLabel),
    h('span', { className: 'reversal-strength ' + r.strCls }, r.strength),
  );
  return h('div', { className: 'reversal-wrap' },
    h('div', { className: 'reversal-col reversal-col-bull' },
      h('div', { className: 'reversal-col-title' }, '↑ Bullish Turns'),
      bulls.length
        ? bulls.map(makeRow)
        : h('div', { className: 'reversal-empty' }, 'No significant shifts'),
    ),
    h('div', { className: 'reversal-col reversal-col-bear' },
      h('div', { className: 'reversal-col-title' }, '↓ Bearish Turns'),
      bears.length
        ? bears.map(makeRow)
        : h('div', { className: 'reversal-empty' }, 'No significant shifts'),
    ),
  );
}

"""

# Inject before MarketOutlook component
INJECT_BEFORE = 'function MarketOutlook('

if 'ReversalWatch' not in content:
    if INJECT_BEFORE in content:
        content = content.replace(INJECT_BEFORE, REVERSAL_COMPONENT + INJECT_BEFORE, 1)
        changes += 1
        print('✓  ReversalWatch component added')
    else:
        print('✗  MarketOutlook not found for component injection')
else:
    print('–  ReversalWatch already present')

# ── 4. Slot ReversalWatch into MarketOutlook render, after dial-grid ─────────
OLD_OUTLOOK_FOOT = "    h('div', { className: 'outlook-foot' },"
NEW_OUTLOOK_FOOT = """    h(ReversalWatch, { data }),
    h('div', { className: 'outlook-foot' },"""

if 'h(ReversalWatch' not in content:
    if OLD_OUTLOOK_FOOT in content:
        content = content.replace(OLD_OUTLOOK_FOOT, NEW_OUTLOOK_FOOT, 1)
        changes += 1
        print('✓  ReversalWatch slotted into MarketOutlook render')
    else:
        print('✗  outlook-foot insertion point not found')
        # Try to find it
        idx = content.find('outlook-foot')
        print(f'   outlook-foot at: {idx}')
        if idx != -1: print(repr(content[idx-50:idx+80]))
else:
    print('–  ReversalWatch already in render')

# ── 5. Pass data prop into MarketOutlook call in TrendMemo ───────────────────
OLD_OUTLOOK_CALL = 'h(MarketOutlook, { data, newsData, fg })'
NEW_OUTLOOK_CALL = 'h(MarketOutlook, { data, newsData, fg })'  # already has data prop — no change needed

# Check if data is passed
if 'MarketOutlook, { data' in content:
    print('–  data already passed to MarketOutlook')
else:
    print('✗  MarketOutlook call does not pass data')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
