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
    print('✗  SECTIONS array not matched — dumping what was found:')
    idx = content.find('const SECTIONS')
    if idx != -1:
        print(repr(content[idx:idx+400]))
    else:
        print('  const SECTIONS not found at all')

# ── 2. Add "How to Use" CSS (before </style>) ────────────────────────────────
HTU_CSS = """
    /* ── How to Use section ─────────────────────────────────────── */
    #how-to-use {
      margin: 0 10px 24px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--surface);
      box-shadow: 0 2px 12px rgba(30,58,138,0.08);
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    #how-to-use summary {
      padding: 11px 16px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #1e3a8a;
      cursor: pointer;
      background: #eff6ff;
      border-bottom: 1px solid #dde5f0;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      list-style: none;
      user-select: none;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    #how-to-use summary::-webkit-details-marker { display: none; }
    #how-to-use summary .htu-arrow { font-size: 0.6rem; opacity: 0.5; transition: transform 0.2s; }
    #how-to-use[open] summary .htu-arrow { transform: rotate(90deg); }
    .htu-body { padding: 16px 18px 20px; }
    .htu-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
      gap: 18px;
    }
    .htu-block { font-size: 0.77rem; line-height: 1.65; color: #374151; }
    .htu-block h3 {
      font-size: 0.68rem;
      font-weight: 700;
      color: #1e3a8a;
      margin-bottom: 7px;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      border-bottom: 1px solid #dde5f0;
      padding-bottom: 4px;
    }
    .htu-block p { margin-bottom: 5px; }
    .htu-wide { grid-column: 1 / -1; }
    .htu-table { width: 100%; border-collapse: collapse; margin-top: 5px; }
    .htu-table td { padding: 4px 8px; vertical-align: middle; font-size: 0.74rem; }
    .htu-table td:first-child { width: 120px; }
    .htu-badge {
      display: inline-block;
      border-radius: 4px;
      font-weight: 800;
      font-size: 0.6rem;
      letter-spacing: 0.04em;
      padding: 2px 8px;
      text-align: center;
      white-space: nowrap;
    }
    .htu-sb  { background: #15803d; color: #fff; }
    .htu-wb  { background: #bbf7d0; color: #14532d; }
    .htu-sw  { background: #fef9c3; color: #854d0e; }
    .htu-wbr { background: #fee2e2; color: #991b1b; }
    .htu-sbr { background: #b91c1c; color: #fff; }
    .htu-dot {
      display: inline-block;
      width: 9px; height: 9px;
      border-radius: 50%;
      vertical-align: middle;
      margin-right: 5px;
      flex-shrink: 0;
    }
    .htu-dot-vs { background: #15803d; }
    .htu-dot-s  { background: #86efac; border: 1px solid #aaa; }
    .htu-dot-u  { background: #fbbf24; }
    .htu-dot-vu { background: #dc2626; }
    .htu-dot-row { display: flex; align-items: center; margin-bottom: 4px; }"""

if '#how-to-use {' not in content:
    if '</style>' in content:
        content = content.replace('</style>', HTU_CSS + '\n  </style>', 1)
        changes += 1
        print('✓  How to Use CSS added')
    else:
        print('✗  </style> not found')
else:
    print('–  How to Use CSS already present')

# ── 3. Add "How to Use" HTML section (before </body>) ────────────────────────
HTU_HTML = """
<section id="how-to-use">
  <details>
    <summary><span class="htu-arrow">&#9654;</span>&#160;&#160;📖 How to Use Indicators — Beginner&rsquo;s Guide</summary>
    <div class="htu-body">
      <div class="htu-grid">

        <div class="htu-block">
          <h3>What Is This Dashboard?</h3>
          <p>This board shows whether each asset is in a bullish or bearish <em>regime</em> using Moving Average (MA) crossover signals — the same method used by professional trend-following funds.</p>
          <p>It doesn&rsquo;t predict the future. It tells you what the trend is <strong>right now</strong> and how stable that trend has been over the past 30 days.</p>
          <p>Hover any coloured signal cell to see a full breakdown of each underlying MA pair.</p>
        </div>

        <div class="htu-block">
          <h3>The Four Signal Columns</h3>
          <p><strong>Coal Mine Canary</strong> — The earliest warning signal, using very fast MAs (3/10 &amp; 5/15 day). Turns bearish <em>first</em> when a trend weakens. Expect false alarms — never act on this alone.</p>
          <p><strong>ST Trend Momo</strong> — Short-term trend over weeks (42–63 day slow MAs vs 10–21 day fast MAs). A strong signal that a move is happening right now.</p>
          <p><strong>LT Trend Momo</strong> — Long-term trend over months (84–252 day MAs). Slower to change, far more reliable. This is the most important column for position decisions.</p>
          <p><strong>All Indicators</strong> — Average of every MA pair combined. The overall momentum health score for the asset.</p>
        </div>

        <div class="htu-block">
          <h3>The Regime Badges</h3>
          <table class="htu-table">
            <tr>
              <td><span class="htu-badge htu-sb">STRONG BULL</span></td>
              <td>All signals aligned bullish. Highest conviction uptrend. Best for long entries.</td>
            </tr>
            <tr>
              <td><span class="htu-badge htu-wb">WEAK BULL</span></td>
              <td>Mostly bullish. Trend is up but not fully dominant. Moderate conviction.</td>
            </tr>
            <tr>
              <td><span class="htu-badge htu-sw">SIDEWAYS</span></td>
              <td>Mixed signals. Market is choppy — low conviction either way. Best to wait.</td>
            </tr>
            <tr>
              <td><span class="htu-badge htu-wbr">WEAK BEAR</span></td>
              <td>Mostly bearish. Trend is down. Consider reducing long exposure.</td>
            </tr>
            <tr>
              <td><span class="htu-badge htu-sbr">STRONG BEAR</span></td>
              <td>All signals bearish. Avoid holding long positions in this asset.</td>
            </tr>
          </table>
        </div>

        <div class="htu-block">
          <h3>The Stability Dot</h3>
          <p>The small dot next to each badge shows how <em>stable</em> that regime has been. It compares today&rsquo;s regime to where it was 10, 20, and 30 days ago.</p>
          <div class="htu-dot-row"><span class="htu-dot htu-dot-vs"></span><span><strong>Dark green</strong> — Regime unchanged 30+ days. Established, reliable trend. Best risk/reward for entries.</span></div>
          <div class="htu-dot-row"><span class="htu-dot htu-dot-s"></span><span><strong>Light green</strong> — Unchanged 10–30 days. Trend is holding and developing.</span></div>
          <div class="htu-dot-row"><span class="htu-dot htu-dot-u"></span><span><strong>Yellow</strong> — Regime changed recently. Watch closely — new trend forming or just noise.</span></div>
          <div class="htu-dot-row"><span class="htu-dot htu-dot-vu"></span><span><strong>Red</strong> — Multiple regime flips in 30 days. Extremely choppy — reduce size or avoid entirely.</span></div>
        </div>

        <div class="htu-block">
          <h3>Balance Sheet Score</h3>
          <p>A fundamental quality score from <strong>0–10</strong>. This is <em>not</em> a price signal — it measures financial strength independently of the trend.</p>
          <p><strong>8–10:</strong> Fortress balance sheet. Net cash, strong free cash flow, minimal debt risk (e.g. AAPL, MSFT, V, CSL).</p>
          <p><strong>5–7:</strong> Solid but with some leverage or a risk factor to monitor (e.g. AVGO, LLY, FMG).</p>
          <p><strong>1–4:</strong> Financial stress, cash burn, or high dilution risk (e.g. PCT, SOUN). Requires extra caution.</p>
          <p>Hover a cell for the detailed rationale. Not applicable to ETFs, crypto, commodities, or forex.</p>
        </div>

        <div class="htu-block">
          <h3>P/E Ratio &amp; News</h3>
          <p><strong>P/E (Price / Earnings)</strong> — How expensive a stock is relative to its earnings. Lower = cheaper, but context always matters. Fast-growing companies naturally trade at higher P/Es than slow-growth or cyclical ones. Hover for context on each ticker.</p>
          <p><strong>News Sentiment</strong> — Scores recent headlines as Bullish, Bearish, or Neutral using keyword analysis (powered by Finnhub). Use as a quick gut-check only — news lags price trends and is inherently noisy. Enter your Finnhub key via <strong>⚙ Keys</strong> to enable live news feeds.</p>
        </div>

        <div class="htu-block htu-wide">
          <h3>Practical Guide: What to Look For</h3>
          <p>✅ <strong>Best setups:</strong> All four columns show STRONG BULL + dark green stability dot + strong balance sheet + reasonable P/E = highest conviction long entries. This combination filters for established uptrends in fundamentally sound assets.</p>
          <p>⚠️ <strong>Early warning:</strong> Coal Mine Canary flips bearish while ST and LT are still bullish = early caution, <em>not yet a sell</em>. Wait for ST Trend Momo to confirm before reducing a position.</p>
          <p>🔄 <strong>New trend forming:</strong> Yellow or red stability dot alongside STRONG BULL = the regime just flipped bullish. It may be genuine — or a false breakout. Wait for the dot to turn light green before committing full size.</p>
          <p>🚫 <strong>What to avoid:</strong> STRONG BEAR across all columns = do not hold long. Red stability dot + STRONG BEAR = the most dangerous environment — trend is consistently down with no sign of reversal.</p>
          <p>📊 <strong>ETFs &amp; crypto:</strong> Balance sheet and P/E won&rsquo;t display (not applicable). Focus entirely on the four trend columns and the stability dot. For crypto especially, the All Indicators column and stability are the primary signals.</p>
          <p>🔁 <strong>Market context first:</strong> Before acting on an individual ticker, check the Global Indices section (SPY, QQQ). If the broad market is in STRONG BEAR, be far more cautious on all long entries regardless of individual signals — even great stocks fall in a market crash.</p>
        </div>

      </div>
    </div>
  </details>
</section>"""

if 'id="how-to-use"' not in content:
    if '</body>' in content:
        content = content.replace('</body>', HTU_HTML + '\n</body>', 1)
        changes += 1
        print('✓  How to Use HTML section added')
    else:
        print('✗  </body> not found')
else:
    print('–  How to Use HTML already present')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed — run this and paste the ✗ lines back to Claude.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Now run: git-push.bat')
