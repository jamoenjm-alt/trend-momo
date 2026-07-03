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
- **One file:** `regime-board.html` (~518 KB), React 18 via esm.sh, **no JSX** (`createElement`
  aliased as `h`), **no build step, no bundler**. `index.html` is a synced published copy.
- Data is **baked into the HTML** by `update-prices.py` (pulls Yahoo daily closes/OHLC, P/E,
  CoinGecko crypto) into marker blocks (`STATIC_PRICES`, `STATIC_OHLC`, `LIVE_PE`). Live
  fallback fetches use CORS proxies (allorigins/codetabs/corsproxy) + Twelve Data + Alpha Vantage.
- **Daily automation:** `update-prices-daily.bat` (Windows Scheduled Task) re-bakes prices,
  commits, and pushes every morning. Now does `git pull` first to avoid push collisions.

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
1. **Editing the 518 KB single file is fragile** — large-file edits have truncated/corrupted it
   before. Any change should be applied by a small script + verified with `node --check`, never a
   blind full-file rewrite. Consider splitting into modules or a tiny build step.
2. **Free data is rate-limited/unreliable** — Twelve Data 800/day, Alpha Vantage 25/day, CORS
   proxies flaky. Live cells can silently show no data. Baked data via the daily task is the
   reliable path; live fallbacks are best-effort.
3. **Weekly RSI divergence uses 5-day resampling, not true weekly OHLC** (`STATIC_WEEKLY` empty).
   Weekly signals drift from real weekly charts. Fix: bake Yahoo `interval=1wk`.
4. **All stock strategy backtests are survivorship-biased** — universe = names that survived to
   2026. A truly proven mechanical stock strategy needs a survivorship-bias-free dataset
   (Norgate/CRSP); Yahoo can't provide delisted names.
5. **Backtests ignore costs/slippage/spread** — real net edge is lower.
6. **BTC signal page is standalone**, not yet a heading in the board nav.
7. **Mobile layout** — desktop is fine; mobile has had issues and needs a pass.
8. **No live QA pass done this session** — recommend checking browser console for errors and
   verifying every column renders on the live site.

## Suggested improvements (roadmap, ranked)
1. **Support/resistance levels** (auto swing highs/lows + round numbers, distance-to-level).
   Highest-value add — a divergence AT support is an A+ setup; in open air it's noise.
2. **Volume confirmation** (relative volume vs 20-day avg) — filters false breakouts, cheap to add.
3. **Integrate the BTC trend signal** as its own board heading; add an equity/watchlist
   "trend status" panel.
4. **True weekly OHLC** for honest weekly divergences.
5. **Earnings-date flags** + **ATR/stop-distance** for turning signals into trade plans.
6. **Daily "what changed" digest** (new divergences, regime flips) emailed via the existing task.
7. **Split the monolith** into maintainable modules or add a minimal build to end the
   large-file-edit fragility.

## Hard constraint for whoever works on this next
Keep the intellectual honesty bar high. This user trades real money. Do NOT present
survivorship-biased or single-regime backtests as "proven." A strategy is only proven if it
beats a real investable benchmark (SPY) risk-adjusted, out-of-sample, net of costs. Most of what
we tested failed that bar — and saying so was the most valuable output.
