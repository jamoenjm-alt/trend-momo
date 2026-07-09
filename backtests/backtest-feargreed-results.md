# Fear/Greed contrarian rotation results

```
==========================================================================
  Contrarian fear/greed rotation — board's own F&G proxy (buyScore)
  Universe: 23 ETFs, 15bps/side, monthly checks, cash 0%
  NOTE: proxy = trend score; news/P-E components have no history.
==========================================================================

V1 max-fear rotation (bottom 5 monthly)
  full: CAGR   8.02%  vol  16.0%  Sharpe  0.56  maxDD  -36.5%   turnover 97%/mo
  1st half: CAGR   6.40%  vol  13.7%  Sharpe  0.52  maxDD  -22.8%
  2nd half: CAGR   9.66%  vol  18.0%  Sharpe  0.60  maxDD  -36.5%

V2 buy fear<=2, sell greed>=8
  full: CAGR   5.18%  vol  13.8%  Sharpe  0.44  maxDD  -29.8%   turnover 17%/mo
  1st half: CAGR   3.29%  vol  12.2%  Sharpe  0.33  maxDD  -18.9%
  2nd half: CAGR   7.12%  vol  15.2%  Sharpe  0.53  maxDD  -29.8%

REF top-5 momentum (prior test)
  full: CAGR   2.70%  vol  11.8%  Sharpe  0.29  maxDD  -27.1%   turnover 99%/mo
  1st half: CAGR   2.24%  vol  10.5%  Sharpe  0.26  maxDD  -23.6%
  2nd half: CAGR   3.16%  vol  12.9%  Sharpe  0.31  maxDD  -27.1%

SPY B&H
  full: CAGR  14.44%  vol  17.1%  Sharpe  0.87  maxDD  -33.7%
  1st half: CAGR  13.84%  vol  14.8%  Sharpe  0.95  maxDD  -18.6%
  2nd half: CAGR  15.05%  vol  19.2%  Sharpe  0.83  maxDD  -33.7%

Per-year returns (V1 / V2 / SPY):
  2010:    0.00% /    0.00% /   17.57%
  2011:   -5.79% /   -3.72% /    0.85%
  2012:   17.85% /   17.08% /   14.17%
  2013:  -10.20% /  -13.94% /   29.00%
  2014:    7.52% /    3.24% /   14.56%
  2015:    1.95% /   -4.95% /    1.29%
  2016:   21.54% /   19.09% /   13.59%
  2017:   16.77% /    9.79% /   20.78%
  2018:   -7.72% /    0.34% /   -5.25%
  2019:   23.45% /   19.40% /   31.09%
  2020:    6.15% /    8.86% /   17.24%
  2021:    4.32% /   -3.53% /   30.51%
  2022:   -7.58% /  -14.58% /  -18.65%
  2023:   18.45% /    3.12% /   26.71%
  2024:   22.56% /   14.82% /   25.59%
  2025:   20.50% /   15.99% /   18.01%
  2026:    3.07% /   14.93% /    9.60%

V2 diagnostics: avg positions 4.0/5, months fully in cash: 12/198

==========================================================================
V1 max-fear rotation (bottom 5 monthly): FAILS the both-halves Sharpe bar
V2 buy fear<=2, sell greed>=8: FAILS the both-halves Sharpe bar
Bar for 'proven': beat SPY Sharpe in full period AND both halves, net of costs.
==========================================================================
```
