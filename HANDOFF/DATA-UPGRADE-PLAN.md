# Data & forecasting upgrade plan (draft, 16 Nov 2026)

Goal: forecasts that are measurably more accurate out-of-sample — not more complicated. Every source below is a
**candidate**: the new session must confirm it is free, still published, licence-compatible with a public site, and
reachable from the sandbox **before** building on it. Nothing here is validated yet.

## A. Biggest accuracy problems today (fix these first)
1. **Regime blindness.** The town fan learns only from 2009–2026 (falling rates). The twin test
   (`twins_results.json`) suggests 5y outcomes in a "expensive + income squeeze" regime are far lower (median +2%
   real vs +15% unconditional). Need: condition forecasts on the macro regime, validated by backtest.
2. **No rate-cycle variable in the international panel.** Dallas Fed has prices and incomes, not policy rates.
3. **Tiny independent sample.** Overlapping 5–10y windows; ~26 independent expensive episodes. More countries
   and longer history reduce this.
4. **No scoring loop.** Nobody checks forecasts against what actually happened each quarter.
5. **Town forecasts not tied to state/national forecasts** — two inconsistent stories on one site.
6. **(Stocks) survivorship bias.** Backtests run on today's watchlist = companies that survived/won. Any stock
   backtest edge is overstated until tested on point-in-time constituents.

## B. Candidate data sources (verify each)
| Source | What it adds | Fixes |
|---|---|---|
| BIS policy rates + BIS residential property prices (long series, incl. Hong Kong) | Rate-cycle conditioning; more countries/episodes | A1–A3 |
| OECD Analytical House Price database (price-to-income, price-to-rent) | Cross-check of Dallas Fed valuation measures; rent yield regime | A1, A3 |
| ABS Lending Indicators (new housing loan commitments, by state, investor vs owner-occ) | Known leading indicator of prices (months ahead) | Nowcast / short horizon |
| ABS Labour Force (unemployment by state) | Recession conditioning; stress test calibration | A1 |
| ABS Building Approvals (by state) | Leads completions → supply 1–2y ahead | Supply term |
| RBA statistical tables (F5/F6 lending rates, E2 debt-to-income, D2 credit) | Serviceability / borrowing-capacity index | A1 |
| APRA quarterly ADI property exposures (investor share, high-LVR, high-DTI lending) | Credit-tightness regime | A1 |
| Weekly auction clearance rates (public headline figures) | High-frequency sentiment, leads prices | Nowcast |
| Westpac-MI consumer sentiment / house price expectations | Sentiment regime | Nowcast |
| Mortgage arrears index (e.g. S&P RMBS arrears) | Forced-selling risk | Downside tail |
| SQM extra series already on its free pages (days on market? discounting? check) | Town-level stress signals | Town fan |
| RBNZ / NZ REINZ series | Better NZ analogue (tax + rate shock) | Policy overlay |

## C. Method upgrades (each must beat naive baselines in rolling-origin backtests, no look-ahead)
1. **Regime-conditioned base rate:** condition the international analogue on valuation decile × rate cycle
   (hiking / peak / cutting) × income trend. Use leave-one-country-out CV to stop overfitting a few episodes.
2. **Short-horizon nowcast (0–12m):** lending commitments + clearance rates + rate changes → next 2–4 quarters.
3. **Hierarchical town fan:** town = state forecast + town-specific deviation, shrunk toward state. Removes the
   inconsistency and inherits regime conditioning.
4. **Quantile models / conformal calibration per regime** instead of one pooled band.
5. **Forecast-scoring ledger:** each quarter record actual vs p10/p50/p90 for every series; publish hit-rate on
   the site. If coverage drifts, widen bands automatically.
6. **(Stocks)** rebuild backtests on point-in-time index constituents; report results net of costs.

## D. Acceptance rule
A change ships only if, out of sample, it improves pinball loss / CRPS vs the current shipped model AND keeps
80%/50% band coverage within ±5pp. Otherwise document it as "tested, rejected" in methodology.md.
