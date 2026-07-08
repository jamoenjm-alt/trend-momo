# CLAUDE.md

Guidance for Claude Code / any AI agent working in this repository.
Last updated: 2026-07-08. If code and this file disagree, trust the code and fix this file.

## Project Overview

A stock/crypto trend-momentum dashboard (`regime-board.html`) modelled on the Jungle Rock
trend memo page, published to https://jamoenjm-alt.github.io/trend-momo/ via GitHub Pages.
No build step, no npm, no framework CLI. Price data lives in `data/prices.json` (fetched at
boot), so the HTML itself is code-only (~200 KB).

**Decision-support board, not an auto-trader.** The owner trades real money. Keep the
intellectual honesty bar high — see PROJECT-BRIEF.md ("Hard constraint").

## Running / Testing

```bash
# View locally — file:// blocks the data fetch, so use the mini-server:
serve.bat                          # serves on localhost:8123 and opens the board

# Syntax-check the embedded JS without a browser (run after EVERY html edit)
python -c "
import re, subprocess
src = open('regime-board.html').read()
m = re.search(r'<script type=\"module\">(.*?)</script>', src, re.DOTALL)
js = re.sub(r'import\s+\{[^}]+\}\s+from\s+\'[^\']+\';\s*', '', m.group(1))
open('/tmp/s.js','w').write('const h=()=>{},useState=v=>[v,()=>{}],useEffect=()=>{},useCallback=f=>f,useRef=()=>({current:null}),Fragment=null,createRoot=()=>({render:()=>{}});\n'+js)
subprocess.run(['node','--check','/tmp/s.js'])
"

# Re-bake all ~270 tickers into data/prices.json (~12 min; also runs daily via GitHub Action)
python update-prices.py

# Publish manual code changes (takes a commit message as argument)
claude-publish.bat feat: my change description
```

## Architecture

### Files

- `regime-board.html` — all code: one `<script type="module">` using React 18 via
  `https://esm.sh/react@18`, no JSX (`createElement as h`).
- `index.html` — byte-for-byte copy of regime-board.html (GitHub Pages serves it).
  `update-prices.py` re-syncs it; after manual edits run `copy regime-board.html index.html`.
- `data/prices.json` — `{ updated, prices, pe, ohlc, weekly }` keyed by board ticker.
  Written by `update-prices.py`. Fetched by `loadStaticData()` at the bottom of the script
  before first render. If the fetch fails (file:// open), live API fallbacks take over.
- `update-prices.py` — Yahoo (equities/ETF/forex) + CoinGecko (crypto) + stockanalysis (P/E)
  → `data/prices.json`. Merge semantics: tickers that fail today keep yesterday's data.
- `.github/workflows/update-prices.yml` — daily bake at 22:00 UTC (8am AEST), commits
  `data/prices.json`. **This is the primary daily updater.**
- `update-prices-daily.bat` — legacy local daily task. Redundant with the Action;
  should stay disabled in Windows Task Scheduler to avoid dual-writer merge collisions.

### Board structure (top to bottom in the script)

1. `WATCHLIST` — 274 rows of `{ ticker, name, cls }`; cls ∈ Watch | Top20 | Crypto |
   Commodity | ASX | HK | Index | Forex | Custom. Sections: Watch 9, US Top 100 (cls
   stays `'Top20'` for back-compat), Crypto 50, Commodity 20, ASX 50, HK 30, Index 9, Forex 6.
2. `SECTIONS` — display order + labels.
3. `BALANCE_SHEET` / `PE_RATIOS` — hand-curated, keyed by board ticker; missing keys
   render N/A (most of the US 100 / ASX 50 are intentionally uncurated).
4. Signal math (`sma`, `signal`, `scoreToRegime`, `computeSignals`, `computeStabilityState`,
   `buyScore`, `valueScore`), RSI divergence, rel-volume.
5. `CRYPTO_COINCAP_IDS` (live crypto fallback ids), `YF_SYMBOL_MAP` (board → Yahoo symbol,
   covers BRK.B, all ASX .AX names, forex =X, DXY).
6. Data fetchers + `loadAll` (React) — static data first, then TD batch / Yahoo / Stooq /
   proxy fallbacks for anything missing.
7. React components; static tab buttons (`.snav-btn`) live in plain HTML near the bottom and
   drive `window._setSnavFilter`. Default tab = Watchlist; there is no "All" tab. A non-empty
   search shows matches across every section regardless of the active tab.

### Ticker conventions

- Board ticker = key everywhere (prices.json, BALANCE_SHEET, PE map). Yahoo symbol mapping
  lives in `ALL_TICKERS` (python) and `YF_SYMBOL_MAP` (JS): `BRK.B→BRK-B`, ASX bare→`.AX`,
  HK already `NNNN.HK`, forex `EURUSD→EURUSD=X`, `DXY→DX-Y.NYB`.
- `SOL.AX` (WHSP) carries its suffix on the board to avoid colliding with crypto SOL.
- Crypto renames handled: `POL` (ex-MATIC, history migrated), `TON` displays "Gram".
- Data key inside React state is `ticker + '__' + cls`, so a ticker can sit in
  multiple sections (AAPL is in Watch and Top20).

### Signal math

Ten MA pairs across four composite columns (1–2 Week 10/3·15/5; 1–3 Month 42/10·50/15·63/21;
3–9 Month 84/21·126/42·168/42; All Signals = all 10). `scoreToRegime` thresholds:
`>0.6 STRONG_BULL, >0.2 WEAK_BULL, >-0.2 SIDEWAYS, >-0.6 WEAK_BEAR, else STRONG_BEAR`.
Stability = Overall regime sampled at −0/−10/−20/−30d.

## Editing Rules (hard-won — do not skip)

- **Never edit the HTML blind.** Read the target section first; apply large changes with a
  small Python script, not the Edit tool (Edit has truncated this file before, and the
  Cowork mount can leave trailing NUL bytes when a tool shrinks a file — check with
  `python -c "print(open('f','rb').read().count(b'\x00'))"` after big edits).
- **Run the node --check snippet after every HTML edit.**
- `computeSignals` must NOT call `computeStabilityState` (infinite recursion). Stability is
  computed separately and merged via `{ ...sigs, stability }`.
- `fetchT` must call `fetch()` internally, never itself.
- News + ASX/HK Alpha Vantage fetches stay fire-and-forget (`(async()=>{})()`), never
  awaited before `setData(newData)`.
- `update-prices.py` writes `data/prices.json` atomically (tmp + `os.replace`). Keep it that
  way — a half-written JSON kills the whole board.
- After changing `regime-board.html`, sync `index.html` before publishing.

## API Keys & Rate Limits

| Service | Where | Free limit | Used for |
|---------|-------|----------