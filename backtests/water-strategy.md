# WATER — strategy spec & backtest

## The theory (why this is the high-conviction bet)
The signal study (`backtest-results.md`) was blunt: **momentum/buyScore is the only thing in this
toolkit with a real, monotonic edge; RSI divergence is noise or worse.** WATER is built on the one
thing that worked, and nothing it didn't.

WATER is a **cross-sectional momentum rotation with a breadth risk-off switch**:
- It holds the handful of strongest names by buyScore (relative strength).
- It rotates monthly as leadership changes — capital flows to strength, like water finding the
  path of least resistance.
- When breadth collapses (most of the board turns bearish) it pulls everything to **cash** —
  this is the part that addresses the exact failure the study exposed: bear legs destroy longs.

Conviction rests on three independent legs pointing the same way: (1) cross-sectional momentum is
the most-replicated anomaly in the academic literature; (2) a trend/breadth regime filter is the
standard, documented way momentum survives bear markets; (3) our *own* point-in-time backtest found
buyScore monotonically predictive and bear regimes brutal. We are not inventing an edge — we are
trading a known one, filtered by our own data.

## Exact rules (all configurable via env vars on the engine)
| Param | Default | Meaning |
|---|---|---|
| Universe | Watch, Top20, ASX, HK, Commodity, Index | tradable equity/ETF names (no crypto/FX in v1) |
| REBAL | 20 | rebalance every ~month (20 trading days) |
| HOLD | 20 | holding period per leg |
| TOPN | 5 | number of names held when risk-on |
| FLOOR | 6 | a name needs buyScore ≥ 6 to be eligible |
| BREADTH | 0.35 | if < 35% of the board is bullish → 100% cash |
| MINBARS | 2400 (10y run) | history required to enter the backtest universe |

Empty holding slots earn 0 (cash). Benchmark = equal-weight buy-hold of the same universe.

## Interim proof (the ~10 months of data currently baked in)
Run point-in-time on the 49-name equity universe in the current file:

| | WATER | Equal-weight market |
|---|---|---|
| Total return | **+29.6%** | +12.8% |
| CAGR (annualised) | 25.9% | 11.3% |
| Max drawdown | **−2.3%** | (much deeper) |
| Time in cash | 20% | 0% |

WATER roughly doubled the market return with a tiny drawdown — the outperformance came mostly from
sitting in cash through the down legs, not from stock-picking genius (it beat the benchmark in only
half the individual months). **This is one year, in-sample, in a single regime. It is a proof the
engine works, NOT the 10-year number.**

## Get the real 10-year number
On your machine (where Yahoo works):

    python water.py

It extracts the live signal math, pulls ~10 years of daily prices, runs the backtest, prints the
10-year return / CAGR / max drawdown, and writes `water-equity.json` (the equity curve).
**Paste me that output** and I'll build the charted "Water" page on its own heading, reading that curve.

## Honest caveats
- 10y excludes names that didn't trade 10y ago (PLTR, SOUN, newer ETFs) — you can't backtest what
  didn't exist. The live page can still trade them going forward.
- No costs/slippage modelled — a real edge is a few % lower.
- Monthly rebalance, long-only, equal-weight — deliberately simple so it's robust, not overfit.

---

## 10-YEAR RESULT (real Yahoo data, run 2026) — Water FAILED

| Config | CAGR | Total | Max DD | vs Buy&Hold |
|---|---|---|---|---|
| **Buy-and-hold (equal weight)** | **18.3%** | **424%** | −24% | benchmark |
| Water (default) | 15.4% | 311% | −31% | **−2.9%/yr** |
| No cash switch | 18.2% | 417% | −31% | −0.2%/yr |
| Top 3 | 18.2% | 416% | −38% | −0.2%/yr |
| Top 8 | 11.6% | 195% | −29% | −6.7%/yr |
| Top 10 | 10.1% | 159% | −30% | −8.2%/yr |
| Quarterly rebalance | 15.8% | 325% | **−18%** | −2.4%/yr |
| Stricter floor 7 | 15.5% | 311% | −31% | −2.9%/yr |
| Looser cash (.5) | 14.6% | 284% | −31% | −3.7%/yr |

**Conclusion: no configuration beat buy-and-hold over 10 years.** The breadth cash switch
cost ~3%/yr with no drawdown benefit. Concentration (Top 8/10) destroyed returns. Only the
quarterly variant improved drawdown (−18% vs −24%) and it still gave up ~100% of total return.

The momentum rotation has **no return edge** over equal-weight holding this universe. The 10-month
proof (+29.6%) was single-regime luck. Do not deploy Water as a return strategy.

Note: the universe is survivorship-biased (these names are on the board in 2026 *because* they won),
which flatters buy-and-hold further. A fair test needs a broad, point-in-time universe.
