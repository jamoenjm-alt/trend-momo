# Mega-cap fear backtest

```
==========================================================================
  Mega-cap fear backtest — point-in-time top-10 by market cap
  15bps/side, monthly. Bar: beat SPY AND the equal-weight basket
  on Sharpe in full period and both halves, net of costs.
==========================================================================

V1 fear rotation (hold 3 most-feared giants)   (turnover 83%/mo)
  full:     CAGR  16.89%  vol  22.5%  Sharpe  0.81  maxDD  -43.8%
  1st half: CAGR  18.61%  vol  15.6%  Sharpe  1.17  maxDD  -16.6%
  2nd half: CAGR  15.19%  vol  27.7%  Sharpe  0.65  maxDD  -43.8%

V2 dip-buy (enter <= 2, exit >= 7)   (turnover 23%/mo)
  full:     CAGR  14.78%  vol  16.6%  Sharpe  0.92  maxDD  -40.3%
  1st half: CAGR  12.43%  vol  10.0%  Sharpe  1.23  maxDD  -13.5%
  2nd half: CAGR  17.16%  vol  21.2%  Sharpe  0.85  maxDD  -40.3%

REF equal-weight all 10 giants (untimed)   (turnover 2%/mo)
  full:     CAGR  18.53%  vol  19.2%  Sharpe  0.99  maxDD  -36.9%
  1st half: CAGR  15.48%  vol  13.4%  Sharpe  1.14  maxDD  -13.2%
  2nd half: CAGR  21.64%  vol  23.6%  Sharpe  0.95  maxDD  -36.9%

SPY B&H
  full:     CAGR  14.49%  vol  17.1%  Sharpe  0.88  maxDD  -33.7%
  1st half: CAGR  13.84%  vol  14.8%  Sharpe  0.95  maxDD  -18.6%
  2nd half: CAGR  15.15%  vol  19.2%  Sharpe  0.83  maxDD  -33.7%

Per-year (V1 / V2 / EW-10 / SPY):
  2010:    0.00% /    0.00% /    0.00% /   17.57%
  2011:   19.80% /   15.76% /    7.43% /    0.85%
  2012:   20.24% /   13.25% /   10.64% /   14.17%
  2013:   26.34% /   16.16% /   28.03% /   29.00%
  2014:    5.96% /   10.06% /   11.96% /   14.56%
  2015:    8.78% /   10.47% /   20.04% /    1.29%
  2016:   40.86% /   19.51% /   16.73% /   13.59%
  2017:   34.45% /   11.23% /   29.89% /   20.78%
  2018:  -11.01% /    1.57% /    0.35% /   -5.25%
  2019:   28.59% /   36.97% /   36.09% /   31.09%
  2020:   24.98% /   28.23% /   30.53% /   17.24%
  2021:   40.18% /   13.25% /   32.48% /   30.51%
  2022:  -40.47% /  -33.54% /  -34.91% /  -18.65%
  2023:   61.42% /   67.56% /   54.83% /   26.71%
  2024:   20.32% /    9.80% /   53.60% /   25.59%
  2025:   25.31% /   26.76% /   31.04% /   18.01%
  2026:    7.94% /   16.45% /    5.38% /   10.55%

==========================================================================
V1 fear rotation (hold 3 most-feared giants): FAILS
V2 dip-buy (enter <= 2, exit >= 7): beats SPY but NOT the untimed basket — timing added nothing
Universe is point-in-time top-10 (approximate, public record); residual
bias small but nonzero. Costs on. No parameters were tuned after running.
==========================================================================
```
