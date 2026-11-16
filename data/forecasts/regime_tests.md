# Regime & momentum tests (16 Nov 2026)

Question (owner): does the forecast ignore the current downturn? Can "twin" economic paths forecast better?
Data: Dallas Fed IHPD hp2602 (real house prices, real disposable income, 12 countries) + **BIS central bank policy
rates** (new: `raw/bis_cbpol_quarterly.csv`, retrieved 16 Nov 2026 from stats.bis.org API v2, WS_CBPOL, monthly →
quarter-end; Ireland pre-1999 unavailable; NL/ES use euro-area rate from 1999). Scripts: `scripts/twins_analysis.py`,
`scripts/regime_backtest.py`, `scripts/momentum_backtest.py`.

## 1. Australia's regime today [S]
Price-to-income 98th pct of own history; real disposable income −0.1% y/y; policy rate +0.56pp y/y (annual
average) and 2.4pp above its own 10-year average. It is a twin on all three counts.

## 2. What twins did next (5y real, descriptive)
| Set | n | Countries | Median | p10 | p90 | P(fall) |
|---|---|---|---|---|---|---|
| All country-years 1985+ | 444 | 12 | +14.8% | −15% | +48% | 28% |
| Expensive (top decile) | 147 | 11 | +10.4% | −22% | +40% | 35% |
| Expensive + rates high/rising | 40 | 11 | −0.9% | −25% | +28% | 52% |
| Expensive + income falling | 24 | 8 | +2.0% | −25% | +26% | 46% |
| All three | 5 | 5 | n too small | | | |

## 3. Does conditioning on the regime forecast better? — NO (not proven)
Rolling-origin backtest, origins 1995–2021, 312 country-forecasts, training only on outcomes known at the origin.
| Model (5y real, log) | MAE median | Avg pinball | 80% coverage |
|---|---|---|---|
| B1 zero real change | 0.204 | — | — |
| U unconditional base rate | **0.176** | **0.0579** | 77% |
| V valuation decile | 0.177 | 0.0579 | 78% |
| V + income | 0.175 | 0.0579 | 79% |
| V + rates | 0.177 | 0.0586 | 78% |
| V + income + rates | 0.171 | 0.0572 | 77% |
The one apparent gain (V+I+R at MIN_N=8) vanishes at MIN_N 5/15/25 and under an alternative rate rule → noise.
**Conclusion:** at 5 years, knowing the regime shifts the historical median a lot (+15% → ~0%) but has not
improved forecast accuracy, because outcomes inside every regime are extremely dispersed. Per project rules it does
not ship. The honest 5y statement is a wide range, not a confident downturn call or a confident boom call.

## 4. Short horizon — momentum DOES work
1-year-ahead real change, rolling OLS, 329 forecasts 1995–2025:
| Model | MAE (log) |
|---|---|
| Zero change | 0.0534 |
| Historical mean | 0.0486 |
| **Last year's change (momentum)** | **0.0426** (−12% vs mean, −20% vs zero) |
| Momentum + rate change | 0.0427 (rates add nothing) |
Latest coefficients: const +1.4%, momentum 0.32. Australia: real prices −0.45% over the last year → ~+1% real next
12 months (point estimate; typical error ±4–5%).

## 5. Implications
- Real forecasting skill is at the short end (momentum, likely also lending/clearance data — next to test with
  quarterly AU data). Long horizons ≈ base rate + honest width.
- Town fan: median is within the range of tested base rates, so "too generous median" is **not proven** (earlier
  claim retracted). Its upper tail (p90 ≈ +90% real at 5y) is wider than any national base rate (+28% to +48%);
  part is legitimate postcode-level dispersion — test town-level tails against national before changing.
- Show the regime twins on the site as **context** ("in 40 similar episodes, half fell"), never as the forecast.
