# Trend Momo — Roadmap

Owner: Jimmy. Live: https://jamoenjm-alt.github.io/trend-momo/
This is the forward plan. Any AI model or developer picking this project up should read
PROJECT-BRIEF.md (same folder) first (what/why/honest backtest findings), then the repo
root's CLAUDE.md + AI-OPERATING-PROTOCOL.md (how to work), then this file (what to do next). Update the status column as things ship —
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

## Pre-registered test — "does fear timing add anything?" (run as ONE session)

Context: the mega-cap fear backtest (`backtests/backtest-megacap-fear.py`, 2026-07-07) found
that timing entries on fear (V1 rotation, V2 dip-buy) did NOT beat the **untimed equal-weight
top-10 basket** (18.5% CAGR, 0.99 Sharpe). Waterflow (that untimed basket) is now shipped.
Before any fear-timed variant is built or displayed, it must clear this pre-registered bar.
Write these rules down and DO NOT change them after seeing results.

### The benchmarks to beat (both, not just SPY)
- SPY buy & hold (full period + H1 + H2).
- **Untimed EW top-10 (Waterflow)** — this is the real null. Beating SPY is not enough;
  fear timing must beat the boring basket, or it added nothing.

### Pass/fail bar (fixed before running)
A variant PASSES only if it beats **both** benchmarks on **Sharpe** in the **full period AND
both halves**, **net of 15bps/side costs**. Any other outcome = FAIL = do not ship, log it in
"Explicitly rejected". No parameter is tuned after seeing results; if you tune, you must re-run
on a fresh split you have not looked at.

### The three (and only three) variants to test — pre-registered
1. **Fear as a sizing modulator, not a selector.** Hold the full EW-10 basket always; scale
   total exposure 80%→120% by the basket's aggregate fear (more feared = more exposure), rest
   to cash/AGG. Hypothesis: buying the basket cheaper adds return without adding names.
2. **Fear = drawdown-from-high percentile**, not the board's composite F&G. Define "fear" as
   each name's current drawdown vs its own 1-yr high, ranked. Hypothesis: a cleaner, less
   reflexive fear proxy times better.
3. **Dip-buy only above the 200-day MA** ("fear within an uptrend"). Enter a top-10 name on
   fear only while it is above its 200d MA; ignore fear signals in downtrends. This is the one
   shape that rhymes with the BTC>200dma signal — the only other rule that ever passed the bar.

### Anti-fudge checklist (tick every box in the results file)
- [ ] Universe is point-in-time (top-10 per calendar year), not today's winners.
- [ ] Costs applied (15bps/side). Turnover reported per variant.
- [ ] Full + H1 + H2 reported for every variant AND both benchmarks.
- [ ] No parameter changed after first look at results (or fresh split used).
- [ ] Verdict states explicitly whether each variant beat BOTH benchmarks, or FAILED.

If none pass: that is a real, publishable result — write "fear timing adds nothing over the
untimed megacap basket" in Explicitly rejected and move on. Do not keep tweaking until something
looks good; that is the exact mistake this protocol exists to prevent.

## Next backtest — weighting optimization (pre-registered)

Idea (owner, 2026-07): instead of equal-weight (10% each), let the top-10 mega-caps carry
DIFFERENT weights (e.g. #1 by market cap at 25%, tapering down), and search weight schemes to
maximise growth-per-drawdown over the full history. Also test universe size (top-10 vs 20 vs 50).
Rules, fixed before running:
- Point-in-time membership AND point-in-time market-cap ranking (no hindsight weights).
- Test on the DEEP history (needs the survivorship-aware fetch), not just 2010-2026.
- Apply the daily-200dma trend filter variant too (it's the only thing that cut drawdown).
- Bar: a weight scheme is only "better" if it beats equal-weight on Sharpe AND on
  growth-per-max-drawdown, in both halves, net of costs. Report turnover.
- Do NOT curve-fit: pick the scheme on the first half, confirm on the second. If it only wins
  in-sample, reject it. Cap any single name at a sane max (e.g. 25%) to avoid one-stock bets.
