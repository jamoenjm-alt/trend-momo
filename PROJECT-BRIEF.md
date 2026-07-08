# Trend Momo — project brief & handoff

Live site: https://jamoenjm-alt.github.io/trend-momo/
Repo: github.com/jamoenjm-alt/trend-momo  (single-file app, published via GitHub Pages)

## What it is
A personal stock/crypto **trend-momentum dashboard** for one retail investor (trades real
money, mostly US + ASX equities and BTC). Modelled on the "Jungle Rock" trend-memo style.
It is a **decision-support board**, not an auto-trader: it reads price data and renders
regime/momentum signals so the user can scan a watchlist quickly.

## What we're trying to achieve
1. An accurate, at-a-glance read of trend/momentum across ~90–105 tickers.
2. Reversal spotting (RSI divergence) that is trustworthy enough to act on.
3. A market-context view (Fear & Greed dials per asset class).
4. **A backtested, genuinely-proven trading program** — the big goal of the latest work.
5. Auto-updating daily with no manual effort, published to a public URL.

## How it's built (important constraints)
- **Code in one file:** `regime-board.html` (~200 KB), React 18 via esm.sh, **no JSX**
  (`createElement` aliased as `h`), **no build step, no bundler**. `index.html` is a synced copy.
- **Data in `data/prices.json`** (since 2026-07-08): `{updated, prices, pe, ohlc, weekly}`
  written by `update-prices.py`, fetched by the page at boot. Live fallbacks (Twelve Data,
  Yahoo, Stooq, CORS proxies, CoinGecko) cover anything missing. Local viewing needs
  `serve.bat` (file:// blocks the JSON fetch).
- **Universe (2026-07-08):** 274 rows — Watch 9, US Top 100, ASX 50, HK 30, Crypto 50,
  Commodities 20, Indices 9, Forex 6. Tab navigation only (no all-in-one page).
- **Daily automation:** GitHub Action (22:00 UTC) re-bakes and commits `data/prices.json`.
  The local `update-prices-daily.bat` scheduled task is redundant and should stay disabled —
  two writers caused the merge-collision commits in the log.

## Signal logic (what the columns mean)
- Trend regimes from 10 moving-average pairs → composite scored via `scoreToRegime`
  (Strong Bull … Strong Bear).
- `buyScore` (0–10): weighted trend composite. **Pure trend, ignores valuation.**
- `valueScore`: buyScore adjusted by P/E.
- Stability dots (4 states): how often the regime flipped in the last ~30 days.
- RSI divergence (daily + weekly): TradingView-style, pivots on the RSI line.
- Fear & Greed per asset class (Market Outlook page) from external APIs.

## Backtest findings (the honest, important part)
We ran point-in-time backtests (no lookahead) on 10 years of data. Results:
- **`buyScore` has a real, monotonic per-stock edge** at 20–60 day horizons — useful for
  filtering/timing individual decisions.
- **RSI divergence is noise** — bullish divergence was *anti-predictive* (right ~27% of the
  time). Do not trade it naked; keep it as context only.
- **"Water" rotation strategy: FAILED.** Over 10y it returned 15.4% CAGR vs buy-and-hold 18.3%,
  with a worse drawdown. No parameter variation beat buy-and-hold.
- **Broad-universe momentum looked great (30%+ CAGR) but is survivorship-biased fiction** — the
  bias-free ETF version did NOT beat SPY. Confirmed a mirage.
- **The one modest, honest edge: a trend-filtered BTC satellite.** SPY + 5–10% BTC held only
  while BTC > its 200-day MA beat SPY on return and Sharpe in both halves of the decade — but
  it rides on BTC's decaying returns (113%→25% CAGR across halves) and slightly higher drawdown.
  Shipped as `btc-signal.html` (live RISK-ON/OFF badge) + `btc-allocation-rule.md`.

## Known problems / limitations (fix candidates)
1. **All stock strategy backtests are survivorship-biased** — universe = names that survived to
   2026. A truly proven mechanical stock strategy needs a survivorship-bias-free dataset
   (Norgate/CRSP); Yahoo can't provide delisted names.
2. **Backtests ignore costs/slippage/spread** — real net edge is lower.
3. **Free live APIs are rate-limited/unreliable** — baked `data/prices.json` is the reliable
   path; live fallbacks are best-effort. If the JSON's `updated` stamp is >1 trading day old,
   the GitHub Action has stalled — check the Actions tab (it went stale Jul 7–8, 2026).
4. **The project folder's file-sync has rolled files back before** (2026-07-08 incident).
   If files look older than the last commit, restore from git before any .bat pushes.
5. **Most of the expanded universe is uncurated** — Balance Sheet / curated P/E cover ~40
   names; the rest show N/A by design.
6. **Mobile layout** — desktop is fine; mobile needs a pass.
7. **BTC signal page is standalone**, not yet a heading in the board nav.

## Roadmap

Moved to **ROADMAP.md** (ranked, with shipped/rejected lists). Fixed since the last brief:
data split out of the HTML (fragility solved), true weekly OHLC baked, live QA pass clean,
274-ticker universe with tab navigation, workflow hardening. See SESSION-2026-07-08.md.

## Hard constraint for whoever works on this next
Keep the intellectual honesty bar high. This user trades real money. Do NOT present
survivorship-biased or single-regime backtests as "proven." A strategy is only proven if it
beats a real investable benchmark (SPY) risk-adjusted, out-of-sample, net of costs. Most of what
we tested failed that bar — and saying so was the most valuable output.
