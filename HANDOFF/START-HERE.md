# START HERE — handoff for a new AI session (written 16 Nov 2026)

This folder exists so a fresh chat knows exactly where the project is. Read this file, then in order:
`/ROADMAP.md` → `/AI-OPERATING-PROTOCOL.md` → `/CLAUDE.md` → `/data/forecasts/methodology.md` → `HANDOFF/DATA-UPGRADE-PLAN.md`.

**This repo is PUBLIC (GitHub Pages serves every file). Never write personal holdings, balances, loans or keys
into any file here.** The owner's portfolio lives only in browser localStorage (`tm_property_portfolio_v1`).

## 1. The owner and how to work with him
- Jimmy, Australian retail investor; trades/invests real money. Wants a critical, zero-BS consultant: push back,
  no agreeing to move forward, prove things with data and history. He explicitly does NOT want you to just adopt
  his view ("I want proven history and data").
- No personalised financial advice or price targets. Every forecast shown on the site carries "Scenario-based
  estimate", a last-updated date, key assumptions and the general-advice disclaimer.
- Publishing: he runs `.\claude-publish.bat <message>` in PowerShell from the project folder (note the `.\`;
  no parentheses in the message). Tell him to hard-refresh (Ctrl+Shift+R) after — GitHub Pages caches ~10 min.

## 2. What exists (live at https://jamoenjm-alt.github.io/trend-momo/)
| Piece | File | Status |
|---|---|---|
| Stock/crypto board | `regime-board.html` (copy to `index.html`) | Working. Signal page has validated per-horizon picks, stretch gauge, section pills. |
| Price bake | `update-prices.py` + `.github/workflows/update-prices.yml` | Made fail-safe 16 Nov (time budget, checkpoints, 2 crons, `if: always()`). **Owner still needs to add repo secret `CG_KEY`** (free CoinGecko Demo key). |
| Property board | `property-board.html` | Working after 16 Nov crash fix. Every Picks-tab panel wrapped in `safe()` (SafeBox error boundary) — keep it that way. |
| Town fan chart | `ForecastFan` in property-board + `data/property-forecast.json` | Live. Hover/tap readout added 16 Nov (publish pending). **Known bias — see §4.** |
| State 10-yr forecasts | `data/forecasts/property_forecast_{STATE}.json` | Built 16 Nov, NOT yet charted on the site. |
| Ask-AI | `ai-worker/` (Cloudflare Worker) | Code done; **owner hasn't deployed** (see `ai-worker/DEPLOY.md`). |
| Property picks | `scorePicks()` | Fundamentals ~90% / trend ~10%, decile-validated (`docs/ROADMAP.md`). |

## 3. Forecast work completed (state level, 2027–2036)
- Models tested with rolling-origin backtests (origins FY2005/2010/2015) vs baselines B1 (no real change) and
  B2 (drift). Fundamentals ridge/ECM **failed**; drift **failed**. Shipped = ½ B1 + ½ valuation-conditioned
  international base rate (Dallas Fed) + policy overlay (2026 negative-gearing/CGT changes, NZ-anchored judgement).
  Beats naive in only 2 of 3 windows. Bands cross-validated to ~80%/50% coverage. States NOT differentiated.
- Full detail: `data/forecasts/methodology.md`, `analogues.md`, `policy_register.md`, `scripts/phase{2,3,4}*.py`.

## 4. Most recent finding — the town fan is too generous (16 Nov 2026)
Owner challenged the fan as too optimistic given the current squeeze. Test: `data/forecasts/scripts/twins_analysis.py`
→ `data/forecasts/twins_results.json`. "Twins" = country-years with price-to-income in the top decile of own history
AND real disposable income falling the prior year (Australia qualifies now: P/I 98th pct; real income −0.1% y/y,
−4.7% since 2021, Dallas Fed hp2602).

| 5-yr REAL outcome | All 444 country-yrs | Top-decile valuation (147) | **Twins (24, 8 countries)** |
|---|---|---|---|
| Median | +14.8% | +10.4% | **+2.0%** |
| p10 / p90 | −15% / +48% | −22% / +40% | **−25% / +26%** |
| P(fall) | 28% | 35% | **46%** |

Town fan at 5y (universe): p50 +23% / p90 +118% / p10 −22% **nominal** (≈ +7% real p50 at ~2.8% CPI, ASSUMPTION).
Verdict: median modestly high, **upside tail far too fat**, downside roughly adequate. Cause: the fan is built only
from 2009–2026 Australian postcode history (one regime of falling rates). Its own pre-widening calibration: 80% band
covered 60% at 3y.
**Caveat:** 24 overlapping cases ≈ handful of independent episodes. Evidence, not proof. Not yet backtested as a
model, so per project rules it does NOT replace the fan yet.
Hiking-cycle twins (general knowledge, rates not in panel — verify): CAN 2021 −22%, GBR 2021 −9%, NLD 2021 +3%,
DNK 1985 −25% (tax-deduction cut + tightening — closest policy twin), NOR 1987 −33%, IRL 2007 −48% (credit bust).

## 5. Open items (priority order)
1. Owner: publish hover readout (`.\claude-publish.bat property chart hover readout`), add `CG_KEY` secret, deploy ai-worker.
2. Regime-conditioned forecasting — see `DATA-UPGRADE-PLAN.md`. Backtest before shipping.
3. Reconcile the town fan with the state forecasts (one forecast language on the site).
4. Forecast-scoring ledger (record actual vs band each quarter; publish hit-rate).
5. Chart the state forecasts per `methodology.md §9`.
6. Uncommitted files from other sessions in `backtests/` — check `git status` and test before every publish.

## 6. Hard rules (summary — full list in ROADMAP §8 and CLAUDE.md)
- No unsourced numbers; label ASSUMPTION / JUDGEMENT. Your training data is stale — verify 2026 policy first.
- Backtest vs naive baselines, no look-ahead; if it doesn't beat them out-of-sample, it doesn't ship.
- Never narrow bands without cross-validated calibration.
- Edit the HTML with Python patch scripts (exact-once asserts), then `node --check` + NUL-byte check.
- Wrap new property-board panels in `safe(name, el)`. Never commit portfolio data or API keys.
- Log changes with dates in ROADMAP §7.
