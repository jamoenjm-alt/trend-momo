# Trend Momo — Roadmap

Owner: Jimmy. Live: https://jamoenjm-alt.github.io/trend-momo/
This is the forward plan. Any AI model or developer picking this project up should read
PROJECT-BRIEF.md first (what/why/honest backtest findings), CLAUDE.md second (how to work
in the repo), then this file (what to do next). Update the status column as things ship —
this document is the single source of truth for project direction.

## Guiding constraints (do not violate)

1. Decision-support, not auto-trading. The owner trades real money on this.
2. No survivorship-biased or single-regime backtest is ever called "proven".
   Proven = beats SPY risk-adjusted, out-of-sample, net of costs.
3. Keep the no-build-step architecture: one HTML file + data/prices.json + python baker.
4. Baked data is the primary data path. Live APIs are fallbacks, never the plan.

## Shipped (done, verified)

| Item | Date |
|------|------|
| Regime board: 10-MA trend composites, stability dots, trend/value scores | 2026-06 |
| RSI divergence (daily + weekly true OHLC) — context only, backtest says anti-predictive | 2026-06 |
| Fear/Greed dials, news sentiment, rel-volume | 2026-06 |
| Backtest program: buyScore edge confirmed; Water rotation + naked divergence rejected | 2026-06/07 |
| BTC>200dma satellite rule (`btc-signal.html`, `btc-allocation-rule.md`) — the one honest edge | 2026-06 |
| The Plan page, Trade Journal vs SPY, Signal page with daily extremes | 2026-07 |
| Daily auto-bake via GitHub Action + Pages publish | 2026-07 |
| **Data split: prices out of HTML into `data/prices.json`** (ends the 500KB-file fragility) | 2026-07-08 |
| **Universe expansion: 274 tickers — US 100, ASX 50, HK 30, Crypto 50, Commodities 20** | 2026-07-08 |
| **Tab-only navigation (no "All" wall); search works across all sections** | 2026-07-08 |
| Workflow hardening: scoped git adds, parameterised publish message, serve.bat | 2026-07-08 |

## Next up (ranked; do them roughly in this order)

1. **Bake the expanded universe.** Trigger the GitHub Action (workflow_dispatch) or run
   `python update-prices.py` locally. Until this runs, ~185 new tickers show live-fallback
   or N/A. Verify `data/prices.json` "updated" stamp and spot-check ASX/HK rows.
   Also verify the Action is actually running daily again (it was stale 2 days on Jul 8).
2. **Kill the dual daily updater.** Disable the local Windows Scheduled Task
   (`update-prices-daily.bat`) and let the GitHub Action be the single writer. The merge
   collisions in the git log all come from running both.
3. **Support/resistance levels** (auto swing highs/lows + round numbers + distance-to-level).
   Highest-value signal add: divergence AT support is an A+ setup; in open air it's noise.
4. **Earnings-date flags + ATR stop-distance** — turns signals into actionable trade plans.
5. **Sector momentum rollup** — with 100 US names on board, group by GICS sector and show
   sector-level regime (breadth: % of sector above 84d MA). Cheap now that the data exists.
6. **Daily "what changed" digest** — regime flips + new divergences, emailed or as a page
   strip. The board already computes flips vs yesterday; persist and surface them.
7. **Balance-sheet coverage for the US top 20 by weight** — curated scores exist for ~40
   names; the biggest uncurated ones now on the board should get entries (or accept N/A).
8. **Mobile layout pass** — known weak; desktop-first is fine but tabs should not overflow.
9. **Watchlist editor UI** — add/remove personal Watch names without editing code
   (custom-ticker localStorage mechanism already exists; extend it to the Watch section).

## Explicitly rejected (do not resurrect without new evidence)

- Water rotation strategy (lost to buy-and-hold over 10y, worse drawdown).
- Trading naked RSI divergence (bullish divergence right ~27% of the time).
- Broad-universe momentum backtests on Yahoo data (survivorship mirage; bias-free ETF
  version did not beat SPY).
- Displaying all ~274 tickers on one page (scanning value collapses; tab navigation instead).

## Data debt / risks

- CoinGecko ids for newly listed coins (HYPE, PI, SKY, MORPHO, JUP, WLD) were set from
  research on 2026-07-08 but unverified against the API — first bake run will confirm;
  any "no data" coin needs its id fixed in `CRYPTO_CG` (update-prices.py) and
  `CRYPTO_COINCAP_IDS` (HTML).
- Commodity ETNs die periodically (UGA, CANE, KRBN are small) — if a bake reports
  "no data" repeatedly, replace the proxy.
- BALANCE_SHEET / PE_RATIOS hand-curation goes stale quarterly; LIVE_PE auto-refresh
  covers the US 100 only.
- The folder sync-rollback incident (2026-07-08) is an open threat: if files ever look
  older than the last commit, restore from git before letting any .bat push.
