# Extension base-rate study (2026-09-20)

**Question.** When a megacap is X% above its 200-day MA, how often / how hard does it
pull back over the next ~3 months, how long until it reverts to the 200MA, and does
RSI or run-length add anything? Descriptive base rates — **not** a timing signal.

**Data.** deep-panel survivors; 104,441 daily observations where the stock was above
its 200MA with ≥126 trading days of forward data. Survivor bias present (understates the
worst crashes). Overlapping windows → point estimates only, no confidence intervals.

## A. How stretched do they normally get
Extension = price / 200d MA − 1. Percentiles: p50 **+9.7%**, p75 +16.6%, p90 +26%,
p95 +35%, p99 **+61%**. So a name ~55% above its line (DELL now) sits around the **97–98th
percentile** — genuinely rare.

## B. Forward 3-month pullback rises with extension — but so does return
| Extension | median dip (next 63d) | P(≥10% dip) | P(≥20% dip) | median return |
|---|---|---|---|---|
| 0–10%  | −4.5% | 21% | 5%  | +2.7% |
| 10–20% | −4.6% | 23% | 6%  | +3.7% |
| 20–35% | −6.2% | 31% | 9%  | +4.3% |
| 35–50% | −7.7% | 41% | 15% | +5.1% |
| 50–80% | −9.0% | 47% | 23% | +5.0% |
| **80%+** | **−12.8%** | **58%** | **39%** | **+9.4%** |

Extension is a **risk gauge, not a return-killer**: the stretched names dip harder *and*
tend to return more. At DELL's ~55% level the base rate is roughly a **coin-flip on a ≥10%
dip and ~1-in-4 on a ≥20% dip within 3 months** — while that bucket also had the highest
forward return. That is the trade-off, quantified.

## C. The most extended names often DON'T snap back
% that touch their 200MA again within a year: 0–10% ext → 90%; 50–80% → 62%; **80%+ → only
55%** (median ~5 months when they do). "Wait for the pullback to the 200MA" would have left
you out ~45% of the time over a year for the most extended names.

## D. RSI / overbought adds NOTHING (important)
Bucketing the same observations by daily RSI(14): forward 3-month dip probability is ~**24%
in every RSI bucket from 0–50 through 80–100**, and forward return ~+3% in every bucket.
**Overbought RSI does not raise pullback odds once a stock is above its 200MA.** This
corroborates the project's earlier rejection of RSI divergence — RSI level is not informative
for timing pullbacks. (Directly answers the "DELL RSI 87" worry: the 87 reading is not,
by itself, evidence a pullback is more likely.)

## E. Run-length: flat, and the scary cell is a mirage
Forward dip is ~−5% regardless of how long the stock has already been above its 200MA. The
"720+ days" bucket shows −25% but **n=118** — effectively one episode; ignore it.

## Bottom line / recommendation
- Extension is worth **showing** as expectation-setting: "this pick is +55% above its 200d
  line (top ~2%); history says ~half see a 10%+ dip and ~1/4 a 20%+ dip within 3 months."
- Do **not** filter on it (tested earlier: caps cut the momentum edge) and do **not** use RSI
  (no predictive value here).
- Use it for **sizing and stops**, not for skipping the entry.
