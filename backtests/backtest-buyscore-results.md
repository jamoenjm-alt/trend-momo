# buyScore backtest results

```
==========================================================================
  buyScore walk-forward backtest — 23 ETFs, 2010-02-01 → 2026-07-02
  top 5, min score 5.0, 15bps/side, monthly rebalance, cash yields 0%
==========================================================================

Strategy (full): CAGR   2.70%  vol  11.8%  Sharpe  0.29  maxDD  -27.1%
SPY B&H  (full): CAGR  14.44%  vol  17.1%  Sharpe  0.87  maxDD  -33.7%
Avg monthly turnover: 99%  (≈1.78%/yr in costs)

1st half  strategy: CAGR   2.24%  vol  10.5%  Sharpe  0.26  maxDD  -23.6%
1st half  SPY B&H : CAGR  13.84%  vol  14.8%  Sharpe  0.95  maxDD  -18.6%

2nd half  strategy: CAGR   3.16%  vol  12.9%  Sharpe  0.31  maxDD  -27.1%
2nd half  SPY B&H : CAGR  15.05%  vol  19.2%  Sharpe  0.83  maxDD  -33.7%

Per-year (strategy vs SPY):
  2010:    0.00%  vs    17.57%  <-- LAGS
  2011:   -0.07%  vs     0.85%  <-- LAGS
  2012:    7.36%  vs    14.17%  <-- LAGS
  2013:   15.31%  vs    29.00%  <-- LAGS
  2014:    9.50%  vs    14.56%  <-- LAGS
  2015:  -17.58%  vs     1.29%  <-- LAGS
  2016:    3.87%  vs    13.59%  <-- LAGS
  2017:    8.20%  vs    20.78%  <-- LAGS
  2018:  -10.87%  vs    -5.25%  <-- LAGS
  2019:    5.48%  vs    31.09%  <-- LAGS
  2020:   20.54%  vs    17.24%
  2021:    7.23%  vs    30.51%  <-- LAGS
  2022:  -14.33%  vs   -18.65%
  2023:    1.24%  vs    26.71%  <-- LAGS
  2024:    3.35%  vs    25.59%  <-- LAGS
  2025:    9.28%  vs    18.01%  <-- LAGS
  2026:    5.56%  vs     9.60%  <-- LAGS

Signal validity: mean forward 21-day return by buyScore bucket
(if buyScore works, higher buckets should earn more — monotonically)
  score 0-1:   1.38%   n=429
  score 1-2:   1.24%   n=338  (breaks monotonicity)
  score 2-3:   1.12%   n=329  (breaks monotonicity)
  score 3-4:   1.26%   n=294
  score 4-5:   0.93%   n=292  (breaks monotonicity)
  score 5-6:   0.81%   n=349  (breaks monotonicity)
  score 6-7:   0.71%   n=615  (breaks monotonicity)
  score 7-8:   0.67%   n=384  (breaks monotonicity)
  score 8-9:   0.41%   n=499  (breaks monotonicity)
  score 9-10:   0.54%   n=366
  score 10-11:   0.35%   n=360  (breaks monotonicity)
Monotonicity breaks: 8 of 10 steps

==========================================================================
VERDICT: strategy LOSES TO SPY on CAGR, LOSES TO SPY on Sharpe, net of costs.
A strategy is only 'proven' if it wins on Sharpe in BOTH halves.
Remember: this is ETF-universe only. Stock-level claims still need
survivorship-bias-free data (Norgate/CRSP).
==========================================================================
```
