"""
apply-fixes.py — patches regime-board.html in-place
Run: python apply-fixes.py   then: git-push.bat
"""
import sys, shutil

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Move Watchlist to first section ───────────────────────────────────────
OLD_SECTIONS = """const SECTIONS = [
  { label: 'Top 20 US',       cls: 'Top20'     },
  { label: 'ASX',             cls: 'ASX'       },
  { label: 'Global Indices',  cls: 'Index'     },
  { label: 'Crypto',          cls: 'Crypto'    },
  { label: 'Commodities',     cls: 'Commodity' },
  { label: 'Forex',           cls: 'Forex'     },
  { label: 'Hong Kong',       cls: 'HK'        },
  { label: 'Watchlist',       cls: 'Watch'     },
];"""

NEW_SECTIONS = """const SECTIONS = [
  { label: 'Watchlist',       cls: 'Watch'     },
  { label: 'Top 20 US',       cls: 'Top20'     },
  { label: 'ASX',             cls: 'ASX'       },
  { label: 'Global Indices',  cls: 'Index'     },
  { label: 'Crypto',          cls: 'Crypto'    },
  { label: 'Commodities',     cls: 'Commodity' },
  { label: 'Forex',           cls: 'Forex'     },
  { label: 'Hong Kong',       cls: 'HK'        },
];"""

if OLD_SECTIONS in content:
    content = content.replace(OLD_SECTIONS, NEW_SECTIONS, 1)
    changes += 1
    print('✓  Watchlist moved to first section')
elif NEW_SECTIONS in content:
    print('–  Watchlist already first section')
else:
    print('✗  SECTIONS not matched')
    idx = content.find('const SECTIONS')
    if idx != -1: print(repr(content[idx:idx+300]))

# ── 2. Tooltip CSS width → 380px ─────────────────────────────────────────────
for old_w in ['width: 260px;', 'width: 300px;', 'width: 320px;', 'width: 350px;']:
    if old_w in content:
        content = content.replace(old_w, 'width: 380px;', 1)
        changes += 1
        print(f'✓  Tooltip {old_w} → 380px')
        break
else:
    if 'width: 380px;' in content:
        print('–  Tooltip already 380px')
    else:
        print('✗  Tooltip width not matched')

# ── 3. panelW → 380 ──────────────────────────────────────────────────────────
for old_p in ['const panelW = 160;', 'const panelW = 260;', 'const panelW = 300;',
               'const panelW = 320;', 'const panelW = 350;', 'const panelW = 420;']:
    if old_p in content:
        content = content.replace(old_p, 'const panelW = 380;', 1)
        changes += 1
        print(f'✓  {old_p} → panelW = 380')
        break
else:
    if 'const panelW = 380;' in content:
        print('–  panelW already 380')
    else:
        print('✗  panelW not found')

# ── 4. Fix tooltip top clipping ───────────────────────────────────────────────
OLD_TOP = "  const top  = y > vph - 200 ? y - 180 : y;"
NEW_TOP = "  const top  = Math.max(8, Math.min(y, vph - 430));"
if OLD_TOP in content:
    content = content.replace(OLD_TOP, NEW_TOP, 1)
    changes += 1
    print('✓  Tooltip top positioning fixed')
elif NEW_TOP in content:
    print('–  Tooltip top already fixed')
else:
    print('✗  Tooltip top not matched')

# ── 5. Redesign Trend td: arrows → colored pill badges with slow MA number ────
OLD_TREND_TD = """h('td', { style: { textAlign: 'center', color: tc, fontWeight: 700, fontSize: '0.65rem' } }, trend != null ? (trend===1?'▲':'▼') : '—')"""
NEW_TREND_TD = """h('td', { style: { textAlign: 'center', padding: '2px 1px' } }, h('span', { style: { display: 'inline-block', minWidth: 28, padding: '2px 6px', borderRadius: '4px', fontWeight: 800, fontSize: '0.62rem', textAlign: 'center', background: trend===1?'#14532d':trend===-1?'#7f1d1d':'#374151', color: trend===1?'#86efac':trend===-1?'#fca5a5':'#9ca3af' } }, trend != null ? slow : '—'))"""

if OLD_TREND_TD in content:
    content = content.replace(OLD_TREND_TD, NEW_TREND_TD, 1)
    changes += 1
    print('✓  Trend td redesigned (pill badges with slow MA)')
elif NEW_TREND_TD in content:
    print('–  Trend td already redesigned')
else:
    print('✗  Trend td not matched')
    idx = content.find("color: tc, fontWeight")
    if idx != -1: print(repr(content[max(0,idx-30):idx+120]))

# ── 6. Redesign Momo td: arrows → colored pill badges with fast MA number ─────
OLD_MOMO_TD = """h('td', { style: { textAlign: 'center', color: mc,  fontWeight: 700, fontSize: '0.65rem' } }, momo  != null ? (momo ===1?'▲':'▼') : '—')"""
NEW_MOMO_TD = """h('td', { style: { textAlign: 'center', padding: '2px 1px' } }, h('span', { style: { display: 'inline-block', minWidth: 28, padding: '2px 6px', borderRadius: '4px', fontWeight: 800, fontSize: '0.62rem', textAlign: 'center', background: momo===1?'#14532d':momo===-1?'#7f1d1d':'#374151', color: momo===1?'#86efac':momo===-1?'#fca5a5':'#9ca3af' } }, momo != null ? fast : '—'))"""

if OLD_MOMO_TD in content:
    content = content.replace(OLD_MOMO_TD, NEW_MOMO_TD, 1)
    changes += 1
    print('✓  Momo td redesigned (pill badges with fast MA)')
elif NEW_MOMO_TD in content:
    print('–  Momo td already redesigned')
else:
    print('✗  Momo td not matched')
    idx = content.find("color: mc,  fontWeight")
    if idx != -1: print(repr(content[max(0,idx-30):idx+120]))

# ── 7. % column: brighter colours for dark background ────────────────────────
OLD_PCT = """h('td', { style: { textAlign: 'right', fontSize: '0.68rem', color: p==null?'#4b5563':parseFloat(p)>=0?'#22c55e':'#ef4444' } }, p!=null?(parseFloat(p)>=0?'+':'')+p+'%':'—')"""
NEW_PCT = """h('td', { style: { textAlign: 'right', fontSize: '0.68rem', fontWeight: 700, color: p==null?'#4b5563':parseFloat(p)>=0?'#4ade80':'#f87171' } }, p!=null?(parseFloat(p)>=0?'+':'')+p+'%':'—')"""

if OLD_PCT in content:
    content = content.replace(OLD_PCT, NEW_PCT, 1)
    changes += 1
    print('✓  % column colours brightened')
elif NEW_PCT in content:
    print('–  % colours already updated')
else:
    print('✗  % td not matched')
    idx = content.find("parseFloat(p)>=0?'+'")
    if idx != -1: print(repr(content[max(0,idx-60):idx+100]))

# ── 8. Inject CSS (tt-table column widths + Signals panel + How to Use) ───────
INJECT_CSS = """
    /* ── tt-table: column widths for 380px tooltip ──────────────── */
    .tt-table { table-layout: fixed !important; width: 100% !important; border-collapse: collapse; }
    .tt-table th, .tt-table td { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 2px 2px; }
    .tt-table th:nth-child(1), .tt-table td:nth-child(1) { width: 22%; }
    .tt-table th:nth-child(2), .tt-table td:nth-child(2) { width: 24%; }
    .tt-table th:nth-child(3), .tt-table td:nth-child(3) { width: 24%; }
    .tt-table th:nth-child(4), .tt-table td:nth-child(4) { width: 30%; }

    /* ── Signals panel ───────────────────────────────────────────── */
    #signals-panel {
      display: none;
      background: #f8faff;
      border-bottom: 2px solid #1e40af;
      padding: 0;
      animation: slideDown 0.2s ease;
    }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
    .sp-inner { max-width: 1400px; margin: 0 auto; padding: 20px 18px 28px; }
    .sp-title { font-size: 0.68rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #1e3a8a; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
    .sp-title::after { content: ''; flex: 1; height: 1px; background: #dde5f0; }
    .sp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 16px; }
    .sp-card { background: #fff; border: 1px solid #dde5f0; border-radius: 8px; padding: 14px 16px; font-size: 0.76rem; line-height: 1.65; color: #374151; }
    .sp-card.sp-wide { grid-column: 1 / -1; }
    .sp-card h3 { font-size: 0.67rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 2px solid; }
    .sp-card.bull h3  { color: #15803d; border-color: #15803d; }
    .sp-card.bear h3  { color: #b91c1c; border-color: #b91c1c; }
    .sp-card.caution h3 { color: #92400e; border-color: #f59e0b; }
    .sp-card.neutral h3 { color: #1e3a8a; border-color: #1e3a8a; }
    .sp-card p { margin-bottom: 6px; }
    .sp-step { display: flex; gap: 10px; margin-bottom: 8px; align-items: flex-start; }
    .sp-step-num { min-width: 20px; height: 20px; border-radius: 50%; font-size: 0.62rem; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }
    .bull .sp-step-num { background: #dcfce7; color: #15803d; }
    .bear .sp-step-num { background: #fee2e2; color: #b91c1c; }
    .sp-chip { display: inline-block; font-size: 0.58rem; font-weight: 800; letter-spacing: 0.04em; padding: 1px 6px; border-radius: 3px; vertical-align: middle; margin: 0 1px; }
    .chip-sb  { background: #15803d; color: #fff; }
    .chip-wb  { background: #bbf7d0; color: #14532d; }
    .chip-sw  { background: #fef9c3; color: #854d0e; }
    .chip-wbr { background: #fee2e2; color: #991b1b; }
    .chip-sbr { background: #b91c1c; color: #fff; }
    .sp-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; vertical-align: middle; margin: 0 2px; }
    .sp-dot-vs { background: #15803d; }
    .sp-dot-s  { background: #86efac; border: 1px solid #aaa; }
    .sp-dot-u  { background: #fbbf24; }
    .sp-dot-vu { background: #dc2626; }
    .sp-warn { background: #fffbeb; border-left: 3px solid #f59e0b; padding: 6px 10px; border-radius: 0 4px 4px 0; margin-top: 6px; font-size: 0.72rem; }

    /* ── How to Use section ─────────────────────────────────────── */
    #how-to-use { margin: 0 10px 24px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); box-shadow: 0 2px 12px rgba(30,58,138,0.08); overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    #how-to-use summary { padding: 11px 16px; font-size: 0.78rem; font-weight: 700; color: #1e3a8a; cursor: pointer; background: #eff6ff; border-bottom: 1px solid #dde5f0; letter-spacing: 0.05em; text-transform: uppercase; list-style: none; user-select: none; display: flex; align-items: center; gap: 8px; }
    #how-to-use summary::-webkit-details-marker { display: none; }
    #how-to-use summary .htu-arrow { font-size: 0.6rem; opacity: 0.5; transition: transform 0.2s; }
    #how-to-use[open] summary .htu-arrow { transform: rotate(90deg); }
    .htu-body { padding: 16px 18px 20px; }
    .htu-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 18px; }
    .htu-block { font-size: 0.77rem; line-height: 1.65; color: #374151; }
    .htu-block h3 { font-size: 0.68rem; font-weight: 700; color: #1e3a8a; margin-bottom: 7px; letter-spacing: 0.07em; text-transform: uppercase; border-bottom: 1px solid #dde5f0; padding-bottom: 4px; }
    .htu-block p { margin-bottom: 5px; }
    .htu-wide { grid-column: 1 / -1; }
    .htu-reg-table { width: 100%; border-collapse: collapse; margin-top: 5px; }
    .htu-reg-table td { padding: 4px 8px; vertical-align: middle; font-size: 0.74rem; }
    .htu-reg-table td:first-child { width: 120px; }
    .htu-badge { display: inline-block; border-radius: 4px; font-weight: 800; font-size: 0.6rem; letter-spacing: 0.04em; padding: 2px 8px; text-align: center; white-space: nowrap; }
    .htu-sb  { background: #15803d; color: #fff; }
    .htu-wb  { background: #bbf7d0; color: #14532d; }
    .htu-sw  { background: #fef9c3; color: #854d0e; }
    .htu-wbr { background: #fee2e2; color: #991b1b; }
    .htu-sbr { background: #b91c1c; color: #fff; }
    .htu-sdot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; vertical-align: middle; margin-right: 5px; flex-shrink: 0; }
    .htu-dot-vs { background: #15803d; }
    .htu-dot-s  { background: #86efac; border: 1px solid #aaa; }
    .htu-dot-u  { background: #fbbf24; }
    .htu-dot-vu { background: #dc2626; }
    .htu-dot-row { display: flex; align-items: flex-start; margin-bottom: 5px; gap: 4px; }
    .htu-dot-row .htu-sdot { margin-top: 3px; }"""

if '#signals-panel {' not in content:
    if '</style>' in content:
        content = content.replace('</style>', INJECT_CSS + '\n  </style>', 1)
        changes += 1
        print('✓  CSS injected (tt-table + signals panel + how to use)')
    else:
        print('✗  </style> not found')
else:
    print('–  CSS already injected')

# ── 9. Inject Signals panel HTML + How To Use + wiring JS ────────────────────
INJECT_HTML = """
<div id="signals-panel">
  <div class="sp-inner">
    <div class="sp-title">📈 Signals Guide — Reading the Indicators</div>
    <div class="sp-grid">

      <div class="sp-card neutral">
        <h3>How the Signal System Works</h3>
        <p>Every cell is calculated from <strong>Moving Average (MA) crossovers</strong> — comparing a fast MA to a slow MA. When price or fast MA is above the slow MA, that signal is bullish (+1). Below = bearish (−1). The regime badge is the average of all relevant signals.</p>
        <p>The columns run fastest to slowest: <strong>Canary</strong> (days) → <strong>ST Trend</strong> (weeks) → <strong>LT Trend</strong> (months) → <strong>All Indicators</strong> (combined).</p>
        <p>Signals are <em>lagging</em> — they confirm a trend that has already started. The edge is in riding confirmed trends, not catching tops and bottoms.</p>
      </div>

      <div class="sp-card bull">
        <h3>Bull Entry Signals (Bear → Bull Reversal)</h3>
        <div class="sp-step"><div class="sp-step-num">1</div><div><strong>Canary turns Bull</strong> while ST and LT still Bear = first alert. Don't enter yet — this flips back often. It's a watch signal only.</div></div>
        <div class="sp-step"><div class="sp-step-num">2</div><div><strong>ST Trend turns Bull</strong> while LT still Bear = building conviction. Canary + ST both bull = consider a small starter position.</div></div>
        <div class="sp-step"><div class="sp-step-num">3</div><div><strong>LT Trend turns Bull</strong> = confirmed trend change. All columns <span class="sp-chip chip-sb">STRONG BULL</span> = highest conviction long entry.</div></div>
        <div class="sp-step"><div class="sp-step-num">4</div><div><strong>Stability dot turns light green</strong> <span class="sp-dot sp-dot-s"></span> = regime has held 10+ days. This is your size-up signal — trend is confirmed, not a false alarm.</div></div>
        <div class="sp-warn">⚡ Fastest reversals: all columns flip bull within days. These are momentum explosions. Enter early but size smaller until LT confirms.</div>
      </div>

      <div class="sp-card bear">
        <h3>Sell &amp; Exit Signals (Bull → Bear Reversal)</h3>
        <div class="sp-step"><div class="sp-step-num">1</div><div><strong>Canary turns Bear</strong> while ST and LT still Bull = early warning. Tighten your stop, reduce 10–20%, watch closely.</div></div>
        <div class="sp-step"><div class="sp-step-num">2</div><div><strong>ST Trend turns Bear</strong> = meaningful exit signal. Canary + ST both bear = reduce 30–50%. Short-term trend has turned against you.</div></div>
        <div class="sp-step"><div class="sp-step-num">3</div><div><strong>LT Trend turns Bear</strong> = confirmed exit. This is the signal to exit the majority of your position.</div></div>
        <div class="sp-step"><div class="sp-step-num">4</div><div><strong>All Indicators <span class="sp-chip chip-sbr">STRONG BEAR</span></strong> = you missed the ideal exit — still exit now. Don't hold hoping for a bounce.</div></div>
        <div class="sp-warn">🔴 Stability dot turns red <span class="sp-dot sp-dot-vu"></span> while bearish = downtrend is well-established and reliable. This is not a dip.</div>
      </div>

      <div class="sp-card neutral">
        <h3>Price Reversal Patterns</h3>
        <p><strong>Momentum Surge (V-shape):</strong> Canary → ST → LT all flip bull within 1–2 weeks. Fast and powerful. High conviction entry once LT confirms. Often follows major news or earnings beats.</p>
        <p><strong>Slow Grind (Staircase):</strong> Each column flips over 2–4 weeks. More reliable. Stability dot progresses yellow → light green → dark green. Best risk/reward entries.</p>
        <p><strong>Bear Trap:</strong> Canary + ST flip bull, stability dot still red <span class="sp-dot sp-dot-vu"></span>, then flip back bear within days. Failed reversal — never size up on a red dot.</p>
        <p><strong>Distribution Top:</strong> Canary goes bear, ST follows a week later, LT holds bull for 2–4 weeks. Classic staged distribution. Exit in stages: reduce at Canary, half-exit at ST, full exit at LT.</p>
      </div>

      <div class="sp-card neutral">
        <h3>Reading Column Combinations</h3>
        <p><span class="sp-chip chip-sb">SB</span><span class="sp-chip chip-sb">SB</span><span class="sp-chip chip-sb">SB</span> + <span class="sp-dot sp-dot-vs"></span> Established uptrend, dark green dot. Highest conviction. Best risk/reward.</p>
        <p><span class="sp-chip chip-sb">SB</span><span class="sp-chip chip-sb">SB</span><span class="sp-chip chip-wbr">WBR</span> + <span class="sp-dot sp-dot-u"></span> Strong short-term, LT still turning. Size smaller until LT confirms.</p>
        <p><span class="sp-chip chip-wbr">WBR</span><span class="sp-chip chip-wbr">WBR</span><span class="sp-chip chip-sb">SB</span> + <span class="sp-dot sp-dot-u"></span> Canary + ST have flipped bear but LT still bull. <em>Key exit warning</em>. Reduce now.</p>
        <p><span class="sp-chip chip-sw">SW</span><span class="sp-chip chip-sw">SW</span><span class="sp-chip chip-sw">SW</span> + <span class="sp-dot sp-dot-vu"></span> All sideways + red dot = choppy. No edge. Do nothing.</p>
        <p><span class="sp-chip chip-sbr">SBR</span><span class="sp-chip chip-sbr">SBR</span><span class="sp-chip chip-sbr">SBR</span> + <span class="sp-dot sp-dot-vs"></span> Dark green dot on bear = sustained downtrend. No longs.</p>
      </div>

      <div class="sp-card caution">
        <h3>What to Be Cautious Of</h3>
        <p><strong>🔴 Red stability dot = no trade.</strong> When the dot is red, the signal is chopping back and forth. Any entry is a coin flip.</p>
        <p><strong>All STRONG BULL = likely late.</strong> By the time every column is STRONG BULL with dark green dot, the easy move has already happened. Look for pullback entries, not chasing.</p>
        <p><strong>Signals lag.</strong> A stock can drop 20% and still show STRONG BULL for a week. Use stops, not signals alone, for risk management.</p>
        <p><strong>Crypto moves faster.</strong> Signals can flip in days not weeks. Higher false-signal rate. Use smaller positions and wider stops.</p>
        <p><strong>Market correlation.</strong> In a broad market crash (SPY STRONG BEAR), almost everything goes red regardless of individual signals. Check Indices first.</p>
        <p><strong>News events.</strong> Earnings or macro data can cause a 1-day spike flipping Canary. If Canary flips but ST/LT don't follow in 3–5 days, it's noise.</p>
      </div>

      <div class="sp-card neutral sp-wide">
        <h3>Quick Reference — Decision Framework</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-top:4px;">
          <div>
            <p style="font-weight:700;color:#15803d;margin-bottom:4px;">✅ BUY / HOLD CONDITIONS</p>
            <p>• LT Trend = <span class="sp-chip chip-sb">STRONG BULL</span> or <span class="sp-chip chip-wb">WEAK BULL</span></p>
            <p>• Stability dot light green <span class="sp-dot sp-dot-s"></span> or dark green <span class="sp-dot sp-dot-vs"></span></p>
            <p>• Canary and ST agree with LT direction</p>
            <p>• SPY / QQQ not in STRONG BEAR</p>
            <p>• Balance sheet score ≥ 6 (individual stocks)</p>
          </div>
          <div>
            <p style="font-weight:700;color:#b91c1c;margin-bottom:4px;">🚫 SELL / REDUCE CONDITIONS</p>
            <p>• Canary turns <span class="sp-chip chip-wbr">WEAK BEAR</span> → tighten stop</p>
            <p>• ST Trend turns bear → reduce 30–50%</p>
            <p>• LT Trend turns bear → exit majority</p>
            <p>• Stability dot red <span class="sp-dot sp-dot-vu"></span> on bearish signal → full exit</p>
            <p>• SPY / QQQ both STRONG BEAR → reduce all longs</p>
          </div>
          <div>
            <p style="font-weight:700;color:#92400e;margin-bottom:4px;">⚠️ STAND ASIDE CONDITIONS</p>
            <p>• All columns = <span class="sp-chip chip-sw">SIDEWAYS</span></p>
            <p>• Stability dot red <span class="sp-dot sp-dot-vu"></span> = choppy, no edge</p>
            <p>• Canary and LT disagree (one bull, one bear)</p>
            <p>• Recent major news event not yet absorbed</p>
            <p>• When unsure — flat is a valid position</p>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>

<section id="how-to-use">
  <details>
    <summary><span class="htu-arrow">&#9654;</span>&#160;&#160;📖 How to Use Indicators — Beginner&rsquo;s Guide</summary>
    <div class="htu-body">
      <div class="htu-grid">
        <div class="htu-block">
          <h3>What Is This Dashboard?</h3>
          <p>This board shows whether each asset is in a bullish or bearish <em>regime</em> using Moving Average crossover signals — the same method used by professional trend-following funds.</p>
          <p>It doesn&rsquo;t predict the future. It tells you what the trend is <strong>right now</strong> and how stable that has been over 30 days. Hover any signal cell to see a breakdown of each MA pair.</p>
        </div>
        <div class="htu-block">
          <h3>The Four Signal Columns</h3>
          <p><strong>Coal Mine Canary</strong> — Earliest warning (3/10 &amp; 5/15 day MAs). Turns first. Expect false alarms.</p>
          <p><strong>ST Trend Momo</strong> — Short-term trend over weeks (42–63 day MAs). Strong signal a move is happening now.</p>
          <p><strong>LT Trend Momo</strong> — Long-term trend over months (84–252 day MAs). Slowest to change, most reliable. Most important column.</p>
          <p><strong>All Indicators</strong> — Average of every MA pair. Overall momentum health score.</p>
        </div>
        <div class="htu-block">
          <h3>The Regime Badges</h3>
          <table class="htu-reg-table">
            <tr><td><span class="htu-badge htu-sb">STRONG BULL</span></td><td>All signals bullish. Highest conviction uptrend.</td></tr>
            <tr><td><span class="htu-badge htu-wb">WEAK BULL</span></td><td>Mostly bullish. Trend up, moderate conviction.</td></tr>
            <tr><td><span class="htu-badge htu-sw">SIDEWAYS</span></td><td>Mixed signals. Choppy — wait for clarity.</td></tr>
            <tr><td><span class="htu-badge htu-wbr">WEAK BEAR</span></td><td>Mostly bearish. Reduce long exposure.</td></tr>
            <tr><td><span class="htu-badge htu-sbr">STRONG BEAR</span></td><td>All signals bearish. Exit longs.</td></tr>
          </table>
        </div>
        <div class="htu-block">
          <h3>The Stability Dot</h3>
          <p>Compares today&rsquo;s regime to 10, 20, and 30 days ago.</p>
          <div class="htu-dot-row"><span class="htu-sdot htu-dot-vs"></span><span><strong>Dark green</strong> — Unchanged 30+ days. Established trend. Best entries.</span></div>
          <div class="htu-dot-row"><span class="htu-sdot htu-dot-s"></span><span><strong>Light green</strong> — Unchanged 10–30 days. Trend holding.</span></div>
          <div class="htu-dot-row"><span class="htu-sdot htu-dot-u"></span><span><strong>Yellow</strong> — Changed recently. Watch closely.</span></div>
          <div class="htu-dot-row"><span class="htu-sdot htu-dot-vu"></span><span><strong>Red</strong> — Multiple flips in 30 days. Choppy — avoid trading.</span></div>
        </div>
        <div class="htu-block">
          <h3>Hover the Tooltip</h3>
          <p>Hover any coloured signal cell to see the <strong>Trend Ladder</strong>. Each row shows one MA pair:</p>
          <p>• <strong>Pair</strong> (e.g. 10/3) = slow MA / fast MA periods in days</p>
          <p>• <strong>Trend</strong> badge = green if price is above the slow MA (bullish), red if below</p>
          <p>• <strong>Momo</strong> badge = green if fast MA is above slow MA (momentum building), red if below</p>
          <p>• <strong>% vs slow</strong> = how far price is above/below the slow MA right now</p>
        </div>
        <div class="htu-block">
          <h3>Balance Sheet, P/E &amp; News</h3>
          <p><strong>Balance Sheet (0–10)</strong> — Financial quality. 8–10 = fortress. 1–4 = stress. N/A for ETFs, crypto, forex.</p>
          <p><strong>P/E</strong> — How expensive vs earnings. Context matters for growth stocks. Hover for detail.</p>
          <p><strong>News</strong> — Headline sentiment via Finnhub. Gut-check only — news lags price. Enter key in ⚙ Keys.</p>
        </div>
        <div class="htu-block htu-wide">
          <h3>Quick Practical Rules</h3>
          <p>✅ All columns STRONG BULL + dark green dot + strong balance sheet = highest conviction long.</p>
          <p>⚠️ Canary goes bear while LT still bull = early warning. Don't sell yet — wait for ST to confirm.</p>
          <p>🔄 Yellow/red dot + new bull signal = unconfirmed. Wait for green dot before sizing up.</p>
          <p>🚫 All STRONG BEAR = exit. Red dot + STRONG BEAR = confirmed sustained downtrend, no longs.</p>
          <p>🔁 Check Global Indices (SPY, QQQ) first. Individual signals are unreliable in a full market crash.</p>
          <p>📖 Click <strong>Signals</strong> in the top nav for the full entry/exit/reversal guide.</p>
        </div>
      </div>
    </div>
  </details>
</section>

<script>
(function() {
  function wireSignalsPanel() {
    var navLinks = document.querySelectorAll('.topbar-nav a');
    var signalsLink = null;
    for (var i = 0; i < navLinks.length; i++) {
      if (navLinks[i].textContent.trim() === 'Signals') { signalsLink = navLinks[i]; break; }
    }
    if (!signalsLink) return false;
    var panel = document.getElementById('signals-panel');
    if (!panel) return false;
    var topbar = document.querySelector('.topbar');
    if (topbar && topbar.parentNode && !panel._wired) {
      topbar.parentNode.insertBefore(panel, topbar.nextSibling);
      panel._wired = true;
    }
    signalsLink.addEventListener('click', function(e) {
      e.preventDefault();
      var isOpen = panel.style.display === 'block';
      panel.style.display = isOpen ? 'none' : 'block';
      signalsLink.style.color = isOpen ? '' : '#fff';
      signalsLink.style.fontWeight = isOpen ? '' : '800';
      if (!isOpen) panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
    return true;
  }
  var attempts = 0;
  var interval = setInterval(function() {
    attempts++;
    if (wireSignalsPanel() || attempts > 50) clearInterval(interval);
  }, 100);
})();
</script>"""

if 'id="signals-panel"' not in content:
    if '</body>' in content:
        content = content.replace('</body>', INJECT_HTML + '\n</body>', 1)
        changes += 1
        print('✓  Signals panel + How to Use + wiring JS added')
    else:
        print('✗  </body> not found')
else:
    print('–  Signals panel already present')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed — run this and paste the ✗ lines back to Claude.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Now run: git-push.bat')
