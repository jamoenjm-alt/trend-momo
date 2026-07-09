# Allocation Lab — weighting-scheme search

Goal: find the weighting of the point-in-time top-10 US mega-caps that maximises growth while
minimising drawdown. Window: last ~15 years (2010-2026), the data we hold. Owner: Jimmy.

## Method (fixed, so results are comparable)
- **Weights attach to market-cap RANK, not to a ticker.** Slot 1 = that year's largest company,
  slot 2 = second largest, etc. Membership + ranking refreshed yearly, point-in-time (no hindsight).
- Monthly rebalance for the scheme search; daily for the trend-filter overlay.
- **Trend-filter overlay:** hold the basket while the S&P is above its 200-day MA; move to cash the
  day it closes below; re-enter when it reclaims. ~5 switches/yr, 5bps/side cost.
- **Metrics:** CAGR (growth), max drawdown (pain), Sharpe (risk-adj return), **Calmar = CAGR/|maxDD|**
  (growth per unit of drawdown — the headline metric for "max growth, lowest drawdown").
- **Anti-overfit rule:** a scheme only counts if it holds up in BOTH halves (H1 2010-18, H2 2018-26).
  Winning only in-sample = rejected. No weight is tuned after seeing the full-period result.

## Results so far (17 schemes, monthly; top overlays, daily)

Ranked by Calmar (growth per drawdown):

| Scheme (weights by rank) | Filter | CAGR | maxDD | Sharpe | Calmar | H1/H2 stable? |
|---|---|---|---|---|---|---|
| Top-3 equal (33/33/33) | daily 200d | 19.3% | -22.7% | 1.09 | **0.85** | to verify |
| User vector 25/15/10/20/5/5/5/5/5/5 | daily 200d | 18.3% | -22.1% | **1.19** | 0.83 | to verify |
| Top-2 equal (50/50) | none | 20.5% | -28.9% | 0.99 | 0.71 | **yes (0.82/0.86)** |
| Equal 10% each | daily 200d | 16.1% | -22.3% | 1.14 | 0.72 | yes |
| Top-3 equal | none | 21.8% | -32.1% | 1.06 | 0.68 | H1>>H2 |
| Top-1 (single stock) | daily 200d | 22.3% | **-46.7%** | 1.02 | 0.48 | no |
| SPY buy & hold (benchmark) | — | 14.6% | -33.7% | 0.89 | 0.43 | — |

### What we've learned
1. **Concentrating into the 2-3 largest names** beats equal-weight on growth-per-drawdown — the very
   biggest (AAPL/MSFT) were high-return AND steadier than the smaller slots (TSLA/GE/financials).
2. **The daily trend filter only helps DIVERSIFIED baskets** (Top-3/Equal/your-vector → ~-22% DD).
   It FAILS on single-stock (Top-1 → -47%): a single name's crash doesn't track the S&P, so the
   filter can't dodge it. **Single-name concentration is a trap.**
3. **The current champion:** top-heavy weighting (Top-3 or the user vector) + daily 200d filter →
   ~19% CAGR at ~-22% drawdown, vs SPY's 14.6% / -34%. Beats the index on BOTH growth and drawdown.
4. Top-2 equal (no filter) is the most H1/H2-robust of the un-filtered schemes.

## Still to test (the search continues)
1. **Verify the filtered winners on the H1/H2 split** (Top-3+filter, user-vector+filter) — the
   un-filtered Top-2 is currently the only proven-robust one; the filtered ones need this gate.
2. **Finer weight grid** — sweep taper/geometric/front-loaded families in small steps and map the
   whole growth-vs-drawdown frontier, not just 17 points.
3. **Universe size:** top-10 vs top-20 vs top-50 (needs a data fetch — more names, less single-name risk).
4. **Deep history (2000, 2008):** the single most important test. The trend filter's real value is a
   2008-style crash, which this 2010-2026 window does NOT contain. Needs a survivorship-aware fetch.
5. **Cap any single slot** (e.g. max 25%) to keep concentration sane, per the owner's instinct.
6. **Then:** wire the winning scheme into the Allocation Models page and build the interactive pie
   editor so weights can be dragged and CAGR/drawdown update live.

## Hard rule
Report the honest winner AND its overfitting risk. A scheme that only wins in one half, or only
without costs, or only in this 15-year mega-cap regime, is NOT "the best" — it's a story. The Calmar
frontier + the H1/H2 gate + the deep-history run are what separate a real edge from a backtest that
happened to like the last 15 years.
