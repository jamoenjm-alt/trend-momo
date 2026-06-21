# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A single-file stock trend momentum dashboard (`regime-board.html`) modelled on the Jungle Rock trend memo page. No build step, no npm, no framework CLI — open the HTML directly in a browser.

## Running / Testing

```bash
# Open in browser (no server needed)
start regime-board.html          # Windows
open regime-board.html           # macOS

# Syntax-check the embedded JS without running a browser
python -c "
import re, subprocess
src = open('regime-board.html').read()
m = re.search(r'<script type=\"module\">(.*?)</script>', src, re.DOTALL)
js = re.sub(r'import\s+\{[^}]+\}\s+from\s+\'[^\']+\';\s*', '', m.group(1))
open('/tmp/s.js','w').write('const h=()=>{},useState=v=>[v,()=>{}],useEffect=()=>{},useCallback=f=>f,useRef=()=>({current:null}),Fragment=null,createRoot=()=>({render:()=>{}});\n'+js)
subprocess.run(['node','--check','/tmp/s.js'])
"

# Bake all 33 tickers into STATIC_PRICES (run from your machine — not the sandbox)
python update-prices.py
```

## Architecture

### Single-file structure (`regime-board.html`)

Everything lives in one `<script type="module">` block using React 18 via `https://esm.sh/react@18`. No JSX — uses `createElement as h`. No Babel. No bundler.

Key layout inside the script (top to bottom):
1. `WATCHLIST` — array of `{ ticker, name, cls }` where `cls` is one of `Watch | Top20 | Crypto | Commodity | ASX | HK`
2. `SECTIONS` — ordered display groups
3. `BALANCE_SHEET` — hardcoded scores/tips, updated periodically (Claude analysis)
4. `PE_RATIOS` — hardcoded P/E ratios, updated periodically
5. Signal math functions (`sma`, `signal`, `scoreToRegime`, `computeSignals`, `computeStabilityState`)
6. Data fetchers (`fetchT`, `fetchAVNews`, `loadAll`)
7. `window.STATIC_PRICES` block — injected by `update-prices.py`
8. React components (`Badge`, `StabilityDot`, `SignalCell`, `TrendLadder`, `BalanceSheetCell`, `PECell`, `NewsCell`, `KeyConfig`, `App`)

### Signal math

Five SMAs: 21d, 42d, 84d, 126d, 252d. Each signal is +1 (fast > slow) or -1. Composite columns average a subset of signals and map via `scoreToRegime`:

| Column | Signals used |
|--------|-------------|
| Short Term (weeks) | price vs 21d/42d/84d, 21d vs 42d, 42d vs 84d |
| Medium Term (1–3 months) | price vs 21d/42d/84d/126d, 42d vs 84d |
| Long Term (6–12 months) | price vs 84d/126d/252d, 84d vs 252d, 126d vs 252d |
| Overall (all signals) | price vs all 5 MAs |

`scoreToRegime` thresholds: `>0.6 → STRONG_BULL`, `>0.2 → WEAK_BULL`, `>-0.2 → SIDEWAYS`, `>-0.6 → WEAK_BEAR`, else `STRONG_BEAR`.

### Stability dots (4 states)

`computeStabilityState(closes)` samples the Overall regime at -0d, -10d, -20d, -30d lookbacks. **Critical**: it calls `computeSignals` on shorter slices — `computeSignals` must never call `computeStabilityState` (infinite recursion). Stability is merged into sigs *after* both are computed separately in `loadAll`.

### Data loading priority (inside `loadAll`)

1. `window.STATIC_PRICES[ticker]` — highest priority, set by `update-prices.py`
2. Twelve Data batch API (8 tickers/request, 700ms between batches) — US/Watch/Commodity
3. Yahoo Finance v8 fallback for any tickers TD failed on (CORS works in most browsers)
4. CoinCap → CoinGecko fallback for crypto
5. Alpha Vantage `TIME_SERIES_DAILY` for ASX/HK (background, non-blocking)
6. Alpha Vantage `NEWS_SENTIMENT` for news column (fire-and-forget background)

### `window.STATIC_PRICES` injection

The block between `// @@STATIC_PRICES_START@@` and `// @@STATIC_PRICES_END@@` is the injection target. `update-prices.py` replaces this entire block using regex. Always preserve both markers and the exact `window.STATIC_PRICES = {...};` format. Data keyed by board ticker (e.g. `"BRK.B"`, not `"BRK-B"`).

### State management

Data key is `ticker + '__' + cls` (e.g. `AAPL__Watch`) so the same ticker appearing in multiple sections (Watch + Top20) loads independently. `data[key]` shape: `{ closes: null|number[], sigs: null|{...}, loading: boolean }`.

## API Keys & Rate Limits

| Service | Key location | Free limit | Used for |
|---------|-------------|------------|---------|
| Twelve Data | `const TD_KEY` in HTML | 800 credits/day, 8 req/min | US/ETF prices |
| Alpha Vantage | `const AV_KEY_DEFAULT` in HTML | 25 req/day, 5 req/min | News sentiment + ASX/HK prices |
| CoinCap | No key | Generous | BTC/ETH daily history |
| CoinGecko | No key | Heavy throttling | BTC/ETH fallback only |
| Yahoo Finance | No key | CORS-accessible | Python script + browser fallback |

When TD credits are exhausted it returns `{"code":429,"message":"..."}` at the top level — `json[ticker]` is `undefined`, causing silent no-data. Run `update-prices.py` to bypass all API limits.

## `update-prices.py`

Fetches all 33 tickers from Yahoo Finance and bakes into `STATIC_PRICES`. Yahoo symbol mapping: `BRK.B → BRK-B`, `BTC → BTC-USD`, `ETH → ETH-USD`, `MQG → MQG.AX`, `A2M → A2M.AX`. CSV mode (`--csv FILE.csv TICKER`) accepts stockanalysis.com history exports.

## Editing Rules

- **All edits to the HTML must be tested with `node --check`** (see syntax check command above) before presenting to the user. Truncation at ~867 lines has occurred before — use Python scripts for large replacements, not the Edit tool.
- `computeSignals` must not call `computeStabilityState`. Stability is always computed separately and merged via `{ ...sigs, stability }`.
- `fetchT(url, ms)` wraps `fetch()` with an AbortController timeout — it must call `fetch(url, ...)` internally, not `fetchT(...)` (would recurse infinitely).
- News and ASX/HK AV fetches must remain fire-and-forget (wrapped in `(async () => { ... })()`). They must not `await` before `setData(newData)` is called.
- Hardcoded data (`BALANCE_SHEET`, `PE_RATIOS`) uses the board ticker as key, not Yahoo symbol. For tickers in multiple sections, one entry covers all.
