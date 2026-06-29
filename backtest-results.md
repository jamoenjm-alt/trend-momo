# Backtest Results — Trend Momo signals

**Method.** Point-in-time replay across all 90 tickers in the baked history (~200 bars each, ~21,000 observations). At every bar, each signal is computed using *only* data up to that bar (no lookahead), then forward returns are measured at +5, +20, and +60 trading days. "Edge" = the signal's average forward return minus the baseline (every bar, same horizon). Strike rate for long signals = % of observations that rose; for short signals = % that fell.

---

## Read this first — the sample is one bear leg

The baseline for this whole dataset is **negative**: −2.7% at 20 days, **−7.6% at 60 days**, only 37.8% of all bars were higher 60 days later. This window is a broad drawdown (ORCL −57% off its high, MSFT, TSLA all down). That distorts everything:

- Long signals look good partly because they picked the *relative* survivors in a falling market.
- Short signals look great because almost everything fell.

**You cannot assume these strike rates hold in a bull or sideways market.** The single most valuable next step is baking 3–5 years of history (multiple regimes) and re-running this. Until then, treat the numbers as directional, not gospel. Observations also overlap heavily (a 60-day return shares 59 days with the next), so the effective independent sample is small — the *monotonicity* below is stronger evidence than any single number.

---

## 1. buyScore — the real signal

Forward return rises cleanly and monotonically with buyScore. This is the finding that matters.

| buyScore | +20d avg | +20d strike | +60d avg | +60d strike | +60d edge |
|---|---|---|---|---|---|
| 0–2 | −4.2% | 38.6% | −11.4% | 30.3% | **−3.9%** |
| 2–4 | −3.7% | 39.8% | −10.1% | 34.1% | −2.6% |
| 4–6 | −2.0% | 45.5% | −4.6% | 43.4% | +2.9% |
| 6–8 | −0.4% | 50.0% | −1.1% | 48.8% | +6.5% |
| **8–10** | **+0.9%** | **51.2%** | **+0.8%** | **54.6%** | **+8.4%** |

Clean staircase across all five buckets and all horizons. That consistency is what tells you it's signal, not noise. buyScore is trend-following / relative-strength by construction — the backtest confirms the trend tends to persist.

## 2. Trend regime — confirms buyScore (they're correlated)

| Regime | +60d avg | +60d strike | +60d edge |
|---|---|---|---|
| STRONG_BULL | −0.1% | 52.2% | +7.4% |
| WEAK_BULL | −2.9% | 45.5% | +4.7% |
| SIDEWAYS | −9.5% | 36.3% | −1.9% |
| WEAK_BEAR | −12.0% | 30.3% | −4.5% |
| STRONG_BEAR | −10.8% | 30.9% | −3.2% |

Same story. Bull regimes outperform, bear regimes get hit. Because regime and buyScore are built from the same MA signals, stacking them adds almost nothing (the combo test confirmed it's redundant).

## 3. RSI divergence — does NOT work as a standalone entry

This is the uncomfortable one. You wanted to read setups off divergences. In this data they are **anti-predictive**:

| Signal | +60d avg | strike | +60d edge |
|---|---|---|---|
| Bull divergence (all) | −14.7% | 26.9% up | **−7.1%** |
| Bull divergence (Strong) | −14.5% | 27.0% up | −7.0% |
| Bear divergence (all) | +0.7% | 40.6% down | — |

Bullish RSI divergence — buying it as a reversal — *lost* 7% vs market and was right only 27% of the time. That's the classic "divergence in a strong trend is a trap": in a downtrend, bullish divergences fire repeatedly and keep failing (catching knives). Bearish divergence was no better — names actually drifted *up* afterward, so it didn't work as a short either.

Critically: **adding a bull divergence to a buyScore 8–10 name did not improve it** (+8.3% edge with-or-without). Divergence contributes zero on top of trend.

**Conclusion: do not trade divergences naked.** Keep them on the page as discretionary context, but the entry decision should come from trend/buyScore, with divergence at most a timing nudge inside an already-confirmed name.

## 4. Best combinations tested

| Config | +60d avg | +60d strike | +60d edge | n |
|---|---|---|---|---|
| buyScore 8–10 | +0.8% | 54.6% | +8.4% | 2145 |
| buyScore 8–10 **+ stable dot** | +1.5% | 53.9% | **+9.1%** | 986 |
| STRONG_BULL + stable | +1.1% | 53.7% | +8.7% | 1522 |
| buyScore ≥6 + long-term up | +0.3% | 51.5% | +7.9% | 3894 |
| buyScore 0–2 (as a short) | −11.4% | **69.8% down** | — | 8654 |

The stability filter adds a small edge (+8.4% → +9.1%) but halves your signal count — a reasonable quality-over-quantity trade, not a game-changer.

---

## Highest-profitability playbook (this regime)

1. **Longs:** buyScore **8–10**, preferably with a stable/very-stable dot. Hold **40–60 days**. ~54% strike, ~+8–9% edge over market. This is a position/swing system, not a day-trade tool — at +5 days there is essentially no edge.
2. **Shorts / avoid:** buyScore **0–2**. In this bear sample ~70% fell over 60 days. Treat the short side as regime-dependent — it almost certainly weakens or inverts in an uptrend.
3. **Divergences:** demote from "signal" to "context." Never the sole reason for a trade.
4. **Horizon discipline:** the edge lives at 20–60 days. Don't use these signals for short-term timing.

## What would make this trustworthy

- Bake **multi-year, multi-regime** history and re-run (the −7.6% baseline proves we only tested a drawdown).
- Model **costs**: spread, slippage, and borrow on shorts — they eat a chunk of an 8% edge.
- Add **drawdown/streak** stats, not just averages — a 54% strike still has ugly losing runs.
- Walk-forward out-of-sample: pick the rule on one period, test it on the next.
