# ROADMAP.md — read this first (every AI agent, every session)

Owner: Jimmy · Live site: https://jamoenjm-alt.github.io/trend-momo/ · Last updated: 16 Nov 2026
Read order: **this file → `AI-OPERATING-PROTOCOL.md` → `CLAUDE.md` → `docs/ROADMAP.md` (board direction, v2)
→ `data/forecasts/methodology.md` (property forecasts).**

## 1. Project purpose and current state
A decision-support website (no build step, GitHub Pages) with two boards:
- **Stock & crypto board** (`regime-board.html` / `index.html`): trend-momentum regimes for ~290 tickers, Signal page
  with validated horizon picks and stretch gauge. Prices baked daily into `data/prices.json` by a GitHub Action.
- **Property board** (`property-board.html`): ~215 Australian towns/cities on SQM weekly data, buy/sell scoring
  (decile-validated), private portfolio tab (localStorage only), Ask-AI panel (needs the Cloudflare Worker in
  `ai-worker/`, not yet deployed).
- Per `docs/ROADMAP.md` v2, **property is the primary board**; equities are the satellite.
- The owner trades and invests real money. **Honesty over polish.** No unvalidated "edge" is ever shown as proven.

## 2. Property forecast feature (10-year, 2027–2036)
**Done (16 Nov 2026):**
- `data/forecasts/policy_register.md` — every policy input, source, retrieval and effective date.
- `data/forecasts/raw/` — all inputs (ABS 6432/6416/3101/5220/8752, RBA F1.1/F5/D1/D2/G1, Dallas Fed IHPD).
- `data/forecasts/scripts/` — `phase2_analogues.py`, `phase3_models.py`, `phase4_final.py` (fully reproducible).
- `data/forecasts/property_forecast_{NSW,VIC,QLD,SA,WA,TAS,NT,ACT}.json` — houses & units, capital & rest-of-state,
  real & nominal, p10–p90, low/base/high scenarios, assumptions. Schema in `methodology.md §8`.
- `methodology.md`, `analogues.md`.

**Key result to respect:** the fundamentals model and drift model **failed** backtests and are not used. The shipped
blend (½ no-real-change + ½ international base rate + policy overlay) beats naive in 2 of 3 windows only. The bands
are cross-validated to ~80%/50% coverage. **States are not differentiated** (nothing validated). Do not "improve"
this by adding an unvalidated model.

**Next (in order):**
1. Build the chart on the property board from the JSON, following `methodology.md §9` display rules exactly.
2. Add the forecast-scoring ledger (see §5 idea #1) so every quarter we check actuals against the bands.
3. Work through the ranked ideas in §5.

**How to refresh (quarterly, after each ABS Total Value of Dwellings release; and immediately after any material
policy or RBA change):**
1. **Re-verify policy first** — Tranche 2 (Tax Reform No. 3 Bill) status at the top of every run, then the rest of
   `policy_register.md §11`. Update the register with new retrieval dates.
2. Re-download `raw/` files from the URLs in `methodology.md §1` (same table numbers; check column titles still
   match — the scripts select by series title).
3. Run: `cd data/forecasts/scripts && python3 phase2_analogues.py && python3 phase3_models.py && python3 phase4_final.py`.
4. Compare the backtest table and calibration to the previous run. If the method changed, re-run the full backtest
   and record it before shipping.
5. Log the run (date, data vintage, what changed) in §7 below.

## 3. Policy watchlist (re-verify before every forecast refresh)
- **Tax Reform No. 3 Bill 2026 ("Tranche 2")** — introduced 14 Oct 2026, NOT law at 15 Nov 2026. Watch: passage,
  amendments to the s960-590 "new residential dwelling" definition, any split of Schedule 5. **Forecasts assume it
  passes substantially as introduced.**
- ATO guidance on s26-155 and the CGT valuation/apportionment method (needed before 1 Jul 2027).
- **RBA:** 8 Dec 2026, then 2027 meetings. Forecasts assume 4.85% is the peak.
- APRA buffer (3pp) and DTI limit (20% at ≥6×) — any change.
- State budgets May–June 2027 (land tax, duty), especially VIC.
- NHSAC quarterly Housing Accord reports; ABS NOM outturns; Home Affairs migration planning levels.
- Federal election (due by 2028) — reversal risk.

## 4. Signals integration spec (forecast → Signals section)
Signals must be honest about what the forecast can and cannot do. Because states are not differentiated, **do not
emit "buy state X" signals from the forecast.** Emit these instead:
| Signal | Trigger | Wording (template) | Colour |
|---|---|---|---|
| Valuation stretch | Australian price-to-income ≥ 90th pct of own history (Dallas Fed) | "Australian housing is more expensive vs incomes than 98% of the time since 1975. Historically, 10-yr real outcomes from here ranged −17% to +62% (10th–90th pct)." | amber |
| Forecast off-track | latest ABS quarter falls outside the p10–p90 band for elapsed horizon in any series | "<Series> is outside its forecast range — the forecast is wrong for this market; treat with extra caution." | red |
| Assumptions stale | cash rate moved ≥50bp, or any policy-register item changed since `generated` | "Forecast assumptions are out of date (<what changed>). Re-run pending." | grey |
| Policy event | Tranche 2 passes/fails/amended; ATO guidance issued | "<event> — forecast to be refreshed." | blue |
| Rent pressure (effect d) | state rent growth ≥ 2× CPI for 4 qtrs (data source to be added) | "Rents rising faster than inflation — consistent with fewer investor-owned rentals." | amber |
Every signal links to `methodology.md` and carries the general-advice disclaimer.

## 5. Ranked feature ideas — accuracy-improving first
Scored 1–5: (a) forecast accuracy, (b) user value, (c) effort (5 = least effort).
| # | Idea | a | b | c | Why |
|---|---|---|---|---|---|
| 1 | Forecast-scoring ledger: each quarter record actual vs band, publish hit-rate | 5 | 4 | 5 | Only way to know if bands stay calibrated; project rule: every forecast has a check date |
| 2 | Rate-cycle-conditioned base rate (add BIS policy rates to the panel; condition on "hiking peak") | 5 | 3 | 3 | Targets failure modes #1–#2 (NZ test) |
| 3 | State-level valuation conditioning (state price-to-income since 1990) — test whether states *can* be ranked | 4 | 5 | 3 | If it validates, unlocks state differentiation |
| 4 | Stratified price series (rebuild a mix-adjusted index from SQM weekly asking prices already in repo, cross-check vs ABS) | 4 | 3 | 3 | Removes composition noise from the target |
| 5 | Add BIS panel incl. Hong Kong; more episodes | 3 | 2 | 4 | Larger analogue sample |
| 6 | New-build price series (ABS new-dwelling CPI component / PPI) → model established vs new | 3 | 4 | 3 | Policy effect (b) currently judgement only |
| 7 | Property-board chart from JSON | 1 | 5 | 3 | User-facing delivery |
| 8 | Rents & vacancy by state into Signals | 2 | 4 | 4 | Effect (d) |
| 9 | Deploy Ask-AI worker (`ai-worker/DEPLOY.md`) | 1 | 4 | 4 | Owner action required |

## 6. Open questions / blockers
- NZ: exact 2021–23 interest-deductibility phase-down for existing properties — secondary sources conflict; confirm on IRD.
- ABS Data API unreachable from the sandbox (spreadsheets used instead).
- No free state-level new-build price series.
- 2026-27 Permanent Migration Program planning level not located.
- APRA DTI/buffer facts are from secondary sources — link APRA's primary letter.
- WA, SA, TAS, ACT, NT 2026-27 state tax changes not individually verified.
- Price bake: set repo secret `CG_KEY` (free CoinGecko Demo key) — see `CLAUDE.md` stale-prices note.
- Uncommitted `ForecastFan` work in `property-board.html` + `data/property-forecast.json` (town-level fan) predates this
  feature — reconcile with the state forecasts before building the chart (one forecast language on the site).

## 7. Change log
- 2026-11-16 — Property board: Houses | Units | All switch + `data/property-types.json` bake (SQM houses_all /
  units_all prices, rents, yields). Typed picks unvalidated (labelled). Fan chart hover readout.
- 2026-11-16 — Added BIS policy rates (`raw/bis_cbpol_quarterly.csv`). Regime-conditioned 5y base rate backtested:
  does NOT beat unconditional base rate (rejected). 1y momentum model beats mean/zero by 12–20% (candidate for
  short-horizon nowcast). Earlier "fan median too generous" claim retracted as unproven. See `regime_tests.md`.
- 2026-11-16 — Twin-episode test (`scripts/twins_analysis.py`): expensive + falling real income → 5y real median
  +2% (p10 −25%, p90 +26%, n=24) vs town fan ≈ +7% real median and much fatter upside. Fan flagged as too generous;
  not replaced (not yet backtested). Hover readout added to fan chart. Handoff in `HANDOFF/`.
- 2026-11-16 — Property forecast v1.0 (state 10-yr bands). Fundamentals and drift models rejected by backtest. Bake
  made fail-safe (time budget, checkpoints, catch-up cron, `if: always()` commit).
- 2026-11-13 — `docs/ROADMAP.md` v2: property primary, decile validation.

## 8. Rules for future agents (non-negotiable)
1. **No unsourced numbers.** Every figure traces to a named source/series ID, or is labelled ASSUMPTION/JUDGEMENT.
2. **Your training knowledge is out of date.** Australian housing policy changed in 2026. Verify current policy
   (Tranche 2 first) against primary sources before any forecast work.
3. **Always backtest before shipping a model change**, against the naive baselines, with no look-ahead. If it does not
   beat them out of sample, it does not ship — say so plainly.
4. **Never narrow the bands** without a cross-validated calibration result.
5. **Log every change with its date** in §7 and in `policy_register.md` where relevant.
6. Never commit personal portfolio data. Never hard-code API keys. Follow `CLAUDE.md` editing rules (Python patches,
   node --check, NUL-byte check, sync `index.html`).
7. Every user-facing forecast carries: "Scenario-based estimate", last-updated date, key assumptions, and the
   general-advice disclaimer.
