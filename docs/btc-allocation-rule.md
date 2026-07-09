# BTC Trend-Satellite — allocation rule (for your own account only)

## The rule
- **Core:** SPY (or your existing equity book).
- **Satellite:** 5–10% allocated to BTC, governed by a single trend filter.
- **Filter:** at each month-end, if BTC's daily close is **above its 200-day moving average**,
  hold the BTC sleeve. If it's **below**, move that sleeve to bonds (AGG) or cash until BTC
  closes back above the 200-day line at a future month-end.
- **Rebalance monthly, not daily.** Daily flip-flopping whipsaws; the backtest used ~monthly.

## What the 10-year backtest showed (2015–2026, date-aligned)
| | CAGR | Max DD (monthly) | Sharpe H1 / H2 |
|---|---|---|---|
| SPY buy & hold | 13.6% | −22.6% | 0.81 / 1.00 |
| SPY + 5% BTC(trend) | 16.8% | −23.4% | 1.12 / 1.07 |
| SPY + 10% BTC(trend) | 20.0% | −24.5% | 1.22 / 1.09 |
| BTC buy & hold (for scale) | 59.0% | **−77% (−83% intraday)** | — |

It beat SPY on return AND Sharpe in **both** halves — the only thing in this whole study to do so.

## The caveats you must hold in mind (do not skip)
1. **BTC's returns are decaying fast:** 113% CAGR in H1 → 25% in H2. From ~$100k it cannot repeat
   its past. Your forward boost will be a fraction of these numbers — use H2 as the optimistic case.
2. **Drawdown is slightly WORSE than SPY**, not better. This adds return for a little more risk;
   it does not reduce risk. BTC's true daily drawdown was −83%; the trend filter softens but does
   not remove it (monthly rebalance means you ride part of a crash before exiting).
3. **Selection bias:** BTC is the one crypto that survived out of thousands. Defensible as "I want
   BTC," not as "a crypto strategy."
4. **This is not financial advice.** It's a backtested rule on your own capital. Position size for
   a −80% BTC move and assume the future is worse than the backtest.

## Recommended setting
5% if you want the Sharpe lift with negligible extra drawdown; 10% if you'll accept ~2% more
drawdown for more return. Above 10% you're mostly betting on BTC's decade repeating — it won't.
