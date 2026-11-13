# Trend Momo — Roadmap (v2, 2026-11-13)

Owner: Jimmy. Live: https://jamoenjm-alt.github.io/trend-momo/
Read order for any AI or developer: PROJECT-BRIEF.md → repo-root CLAUDE.md + AI-OPERATING-PROTOCOL.md
→ this file. Previous version preserved as `ROADMAP-2026-07-09.md`. Update the status column as
things ship — this document is the single source of truth for project direction.

## Guiding constraints (do not violate)

1. Decision-support, not auto-trading. The owner trades real money on this.
2. No survivorship-biased or single-regime backtest is ever called "proven".
   Proven = beats the real benchmark risk-adjusted, out-of-sample, net of costs, **in every era**.
3. Keep the no-build-step architecture: one HTML file per board + baked JSON + python baker.
4. Baked data is the primary data path. Live APIs are fallbacks, never the plan.
5. **Every forecast is a number with a date and a check date.** If it can't be scored, it isn't a forecast.

## What changed in v2 — the reframe

The July roadmap was organised around stock trend-momentum. The evidence since then says the
project's real edge is elsewhere:

| Signal | Validation | Verdict |
|---|---|---|
| Property buy-score (SQM, postcode level) | 139 monthly cross-sections 2014→2026, **9/9 monotone deciles at 6/12/24/36m**, positive in **every era**, 60–81% survives state-neutralisation; driver is rental tightness (vacancy, yield %ile, listings, rent growth), **not** price momentum (which is negative) | **Real, multi-regime edge** |
| BTC > 200-day MA satellite | Beat SPY on return and Sharpe in both halves | Honest, modest, decaying |
| Equity `buyScore` | Monotone per-stock edge at 20–60d | Useful filter, not a program |
| RSI divergence | Anti-predictive (~27% right) | Context only — hide from default view |
| Water rotation, broad momentum, fear timing | Failed their own bars | Rejected |

So: **property becomes the primary board; equities become the satellite.** And "more precision"
comes from three things, none of which is a new signal: **measured calibration, fresh data, and
every forecast linked to a decision.**

The top-1 picks readout (`property-picks-history.json`, 36 months, 26/36 WA) was a single
macro bet counted 36 times. The decile validation (`property-decile-validation.py`, added
2026-11-13) is the honest readout and runs on fresh history in the Action every bake.

## Shipped (done, verified)

| Item | Date |
|------|------|
| Regime board, RSI divergence (context only), F&G dials, news, rel-volume | 2026-06 |
| Backtest program: buyScore edge confirmed; Water / naked divergence / broad momentum rejected | 2026-06/07 |
| BTC>200dma satellite rule (`btc-signal.html`, `btc-allocation-rule.md`) | 2026-06 |
| The Plan page, Trade Journal vs SPY, Signal page | 2026-07 |
| Data split: prices out of HTML into `data/prices.json`; daily Action bake | 2026-07-08 |
| Universe 274 tickers; tab-only navigation; workflow hardening | 2026-07-08 |
| Property board: SQM weekly bake, 650+ postcodes, scorePicks, portfolio tab (localStorage) | 2026-07/08 |
| Property picks backtest (3y, top-1) → `property-picks-history.json` | 2026-08 |
| Loading-hang fix: boot-fetch timeout + plain-JS watchdog on both boards | 2026-09-20 |
| Ask-AI panel on property board (`ai-worker/`) | 2026-10-29 |
| **Full-window decile validation + formula cross-check, wired into the property Action** | **2026-11-13** |

## Next up — ranked. Do them roughly in this order.

### Tier 1 · Fix what's measurably wrong (days)

| # | Item | Status |
|---|------|--------|
| 1 | **Decile view replaces top-1 pick on the property board.** Read `backtests/property-decile-results.json`; show every eligible market's decile and the fitted forward-excess (D9 ≈ +11.7pp/24m, D0 ≈ −7.8pp). Top-decile basket replaces "best buy". | open |
| 2 | **Pinned markets strip** at the top of the property board: TOM/SEA/ARD + NRA/ULL/WOL/BAY/GOS with live decile placement, from the same JSON. Non-personal (postcodes), safe to commit. | open |
| 3 | **Tripwire alarm states.** Armadale vacancy ≥1.8% or rent growth <0 → visible ALARM, not a number to remember. Pattern reusable for the macro tripwires in Tier 3. | open |
| 4 | Kill the dual daily updater — confirm `update-prices-daily.bat` is disabled in Task Scheduler. (July item, never closed.) | open |
| 5 | Hide RSI divergence from the default board view (keep as a toggle). Anti-predictive by our own test; it shouldn't be front-and-centre on a decision tool. | open |

### Tier 2 · Forecast precision — the engine (weeks)

| # | Item | Status |
|---|------|--------|
| 6 | **Prediction Ledger on the site.** `data/ledger.json` + Ledger page: ID, date, owner, probability, check date, outcome. **Seeded 13 Nov (37 public-market calls, v1.1).** Personal-property calls stay out of the repo. Page still to build. | seeded |
| 7 | **Auto-scoring** for anything the repo already has data for: BTC, S&P, every SQM postcode. Pending → scored on the check date without a human. | open |
| 8 | **Brier score per forecaster, running.** This is the precision metric. You can't improve calibration you don't measure. | open |
| 9 | **Consensus capture.** Each call stores what banks / futures / RBA said at the time. Headline = **excess over consensus** (10 recorded in 2026, 0 fully right — that's the real edge). | open |
| 10 | **Factor-level property forecasts with distributions.** Vacancy-trajectory model → 12/24m excess, published as p10/p50/p90 per postcode from the historical outcome spread. No point estimates. | open |
| 11 | **State overlay.** ~40% of 24m edge was the state call. Show raw and state-neutral side by side; surface state regime (e.g. "Perth leading national decline") on a postcode board. | open |
| 12 | Daily "what changed" digest — regime flips, decile moves, tripwires tripped, ledger items due. (July item 6, now has a home.) | open |

### Tier 3 · Proprietary data — what nobody else can copy (ongoing)

| # | Item | Status |
|---|------|--------|
| 13 | **2540 rental-tightness log.** Private form on the portfolio tab: weekly days-to-let, enquiries, rental listings count for Huskisson/Vincentia/Tomerong. Leads SQM by 4–8 weeks in the one postcode that matters. localStorage only — **never commit.** | open |
| 14 | **Macro tripwire panel.** Cash rate 5.10%, unemployment 5.5%, buffer floors, Seaford unlet by 31 Dec — live, with TRIPPED state. Cash rate is 4.85% as of 3 Nov 2026: one hike from the first wire. | open |

### Tier 4 · Equities — demote, don't delete

| # | Item | Status |
|---|------|--------|
| 15 | Only two live equity signals on the default view: `buyScore` and BTC>200dma. | open |
| 16 | Run the two pre-registered tests below exactly as written. If they fail, log in Rejected and stop. | open |
| 17 | **Paper-trading gate = Brier score.** Every paper trade is a ledger entry with a probability and check date; the 12-month trading-exit decision rests on measured calibration, not P&L feel. | open |
| 18 | Mobile layout pass (July item 8). | open |
| 19 | Support/resistance, earnings flags + ATR, sector rollup, balance-sheet curation, watchlist editor (July items 3/4/5/7/9) — parked below everything above. | parked |

## Explicitly rejected (do not resurrect without new evidence)

- Water rotation strategy (lost to buy-and-hold over 10y, worse drawdown).
- Trading naked RSI divergence (bullish divergence right ~27% of the time).
- Broad-universe momentum backtests on Yahoo data (survivorship mirage).
- Displaying all ~274 tickers on one page.
- **Top-1 pick as the property readout** — single-regime presentation of a multi-regime signal.
- **Adding tickers or signals as a route to "more precision."** Every added signal so far failed its own bar; precision comes from calibration, fresh data and decision linkage.
- **Any forecast that is not a number with a date.**

## Data debt / risks

- `data/property-history.json` is gitignored by design (4 MB). It is fresh **only on the Action
  runner**. Local backtests use a stale copy unless `update-property.py` is run by hand (~30 min).
  The committed `property-decile-results.json` is the fresh artefact — read that, not local history.
- SQM revises history. Today's series may not match what was printable at the time — the one
  bias the decile validation cannot remove without archived vintages.
- Index ≠ tradeable. ~8% round-trip on a house means the property signal is a **24-month-plus**
  decision input; the 6m spread does not cover costs.
- CoinGecko ids for newly listed coins unverified until a bake confirms; commodity ETNs die
  periodically; BALANCE_SHEET / PE curation goes stale quarterly.
- The folder-sync rollback incident (2026-07-08) remains an open threat: if files look older
  than the last commit, restore from git before any .bat pushes.
- `git` from the Cowork device shell cannot reach GitHub (proxy). Pull/publish from a normal
  terminal via `claude-publish.bat`.

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

## Pre-registered — property decile validation (ADDED 2026-11-13, already run)

Bar, fixed before the first run: a cross-sectional signal is real only if (a) deciles are
monotone at every horizon, (b) top-minus-bottom is positive in every era, (c) a material share
survives state-neutralisation, (d) it is not explained by trailing price momentum.
Result: (a) 9/9 at 6/12/24/36m · (b) 100% of months in all five eras · (c) 60–81% ·
(d) momentum alone is negative. **PASS.** Re-runs automatically on every property bake; if any
future run fails (a) or (b), the Action output will show it and the decile view must be pulled.
