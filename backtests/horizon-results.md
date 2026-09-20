# Buys-by-hold-period — pre-registered backtest (2026-09-20)

**Question.** For the Signal-page "best buy by how long you'll hold it" panel, which
indicator works best at each hold length (1wk / 1mo / 6mo / 1yr / 5yr)?

**Data.** `deep-panel.json` — 27 survivor mega/large-cap equities, 2001–2026 (SPY, AGG,
BTC excluded). Survivorship-biased, so **absolute returns are optimistic**. To neutralise
that, every pick is judged against the **equal-weight average of the same names** (the null
carries the same bias, so only the *selection* edge survives the comparison).

**Method.** One top pick per indicator at monthly rebalances, held H days, 15bps/side
round-trip cost, split into first/second half of history. A rule earns a non-grey tier only
if it beats the equal-weight null in **both halves**. Headline metric = **beat-avg-stock %**
(bias-robust), not the survivor-inflated absolute return.

## Result — one engine wins everywhere it matters

6-month (126-day) price momentum, held only while the stock is above its 200-day MA, is the
best or tied-best rule at every hold from 1 month to 1 year. Lookback does **not** shift with
hold length (grid test), so per-timeframe "different indicators" would be fitting noise.
Tested alternatives that **lost**: short-term reversal (REV5/REV21), 3-month momentum at a
1-month hold (47% — anti-predictive), long-term reversal, raw board composites, buyScore.

| Hold | Live rule | beat-avg-stock | median excess | tier |
|------|-----------|:--:|:--:|:--:|
| 1 Week  | trend distance vs 200d MA        | ~50% | +0.2 pp | **noise** (coin-flip) |
| 1 Month | 6-mo momentum, uptrend            | 56%  | +1.0 pp | weak |
| 6 Months| 6-mo momentum, uptrend            | **61%** | **+5.2 pp** | **edge** (both halves) |
| 1 Year  | 6-mo momentum, stable uptrend     | 56%  | +2.9 pp | weak, fat-tailed |
| 5 Years | 6-mo momentum, stable uptrend     | ~52% | +10.6 pp | **survivorship, not skill** |

**Honest verdict.** Genuine selection edge only at ~6 months. 1-month and 1-year are thin
(the 1-year mean looks big but that's a handful of NVDA-type windows, not consistency —
beat-avg is only 56%). 1-week is noise. The 5-year "beats SPY 68%" is survivors soaring, not
foresight — you cannot know the survivors in advance, and one name for 5 years is
uncompensated single-name risk → diversify (Allocation Models).

Scripts: `horizon-lab.py` (indicator menu), `horizon-lookback-grid.py` (lookback×hold),
`horizon-card-rules.py` + `horizon-final-stats.py` (exact live-rule validation).
No parameter was tuned after seeing results.
