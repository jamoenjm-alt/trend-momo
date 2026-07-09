#!/usr/bin/env python3
"""
backtest-feargreed.py — contrarian rotation on the board's own fear/greed proxy.

HYPOTHESIS (user's): buying max fear and selling into max greed across asset
classes is a large edge.

WHAT "FEAR/GREED" MEANS HERE — be honest about this: the board's per-ticker
Fear & Greed is tickerGreed() = buyScore*10, nudged by news sentiment and P/E.
News has no queryable history and P/E doesn't apply to bonds/gold, so the
testable point-in-time proxy is buyScore itself: LOW score = fear, HIGH = greed.
This is inverse trend-momentum, which is exactly what the signal-validity table
in backtest-buyscore-results.md pointed at (low buckets out-earned high ones).

PRE-REGISTERED VARIANTS (fixed before running — do not tune afterward):
  V1  Max-fear rotation: each month hold the 5 LOWEST-scoring ETFs, equal weight.
  V2  Buy fear, sell greed: buy score <= 2.0 (deep fear, up to 5 slots, most
      feared first); sell any holding once its score >= 8.0 (greed). Idle slots
      sit in cash at 0%.
  REF Top-5 momentum (the strategy that already failed) and SPY buy-and-hold,
      same calendar, for comparison.
Costs: 15 bps/side on turnover, same as the momentum test.

Uses the same exact-ported signal math and cached data as backtest-buyscore.py.
Results are written to backtest-feargreed-results.md.
"""

import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("bt", os.path.join(HERE, "backtest-buyscore.py"))
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

TOP_N = 5
FEAR_ENTRY = 2.0   # V2: buy at or below this score
GREED_EXIT = 8.0   # V2: sell at or above this score
COST = bt.COST_BPS / 10000.0


def run_variant(data, select_fn, stateful=False):
    """Generic monthly-rebalance engine. select_fn(scores, holdings) -> new weights."""
    calendar = bt.build_calendar(data)
    aligned = bt.align(data, calendar)
    rebs = [i for i in bt.month_starts(calendar) if i > 0]
    equity = [1.0]
    eq_dates = []
    holdings = {}
    turnover_total = 0.0
    picks_log = []
    for k, r in enumerate(rebs):
        scores = bt.scores_on(aligned, calendar, r - 1)
        new_w = select_fn(scores, dict(holdings))
        tickers = set(new_w) | set(holdings)
        turn = sum(abs(new_w.get(t, 0) - holdings.get(t, 0)) for t in tickers)
        turnover_total += turn
        equity[-1] *= (1 - turn * COST)
        holdings = new_w
        picks_log.append((calendar[r], sorted(holdings)))
        r_next = rebs[k + 1] if k + 1 < len(rebs) else len(calendar) - 1
        for i in range(r, r_next):
            day_ret = 0.0
            for t, w in holdings.items():
                c0, c1 = aligned[t][0][i], aligned[t][0][i + 1]
                if c0 and c1:
                    day_ret += w * (c1 / c0 - 1)
            equity.append(equity[-1] * (1 + day_ret))
            eq_dates.append(calendar[i + 1])
    all_dates = [calendar[rebs[0]]] + eq_dates
    return calendar, equity, all_dates, turnover_total, len(rebs), picks_log


def sel_max_fear(scores, _holdings):
    """V1: five lowest scores, equal weight."""
    ranked = sorted(scores.items(), key=lambda kv: kv[1])[:TOP_N]
    return {t: 1.0 / TOP_N for t, _ in ranked}


def sel_fear_to_greed(scores, holdings):
    """V2: keep holdings until greed; fill free slots with deep fear."""
    kept = {t: 1.0 / TOP_N for t in holdings if scores.get(t, 10.0) < GREED_EXIT}
    free = TOP_N - len(kept)
    if free > 0:
        candidates = sorted(
            ((s, t) for t, s in scores.items() if s <= FEAR_ENTRY and t not in kept))
        for s, t in candidates[:free]:
            kept[t] = 1.0 / TOP_N
    return kept


def sel_top_momentum(scores, _holdings):
    """REF: the already-tested top-5 momentum, for side-by-side comparison."""
    eligible = sorted(((s, t) for t, s in scores.items() if s >= bt.MIN_SCORE), reverse=True)
    return {t: 1.0 / TOP_N for _, t in eligible[:TOP_N]}


def main():
    data = bt.load_data("--refresh" in sys.argv)
    if bt.BENCHMARK not in data:
        print("No benchmark data.")
        sys.exit(1)

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    variants = [
        ("V1 max-fear rotation (bottom 5 monthly)", sel_max_fear),
        (f"V2 buy fear<={FEAR_ENTRY:.0f}, sell greed>={GREED_EXIT:.0f}", sel_fear_to_greed),
        ("REF top-5 momentum (prior test)", sel_top_momentum),
    ]

    emit("=" * 74)
    emit("  Contrarian fear/greed rotation — board's own F&G proxy (buyScore)")
    emit(f"  Universe: {len(data)} ETFs, {bt.COST_BPS}bps/side, monthly checks, cash 0%")
    emit("  NOTE: proxy = trend score; news/P-E components have no history.")
    emit("=" * 74)

    results = {}
    for name, fn in variants:
        calendar, equity, dates, turnover, n_rebs, picks = run_variant(data, fn)
        m = bt.metrics(equity, dates)
        results[name] = (equity, dates, m, turnover / n_rebs, picks)

    # SPY benchmark on V1's calendar
    v1_eq, v1_dates = results[variants[0][0]][0], results[variants[0][0]][1]
    b_eq = bt.bench_equity(data, bt.build_calendar(data), v1_dates)
    m_b = bt.metrics(b_eq, v1_dates)

    emit("")
    for name in results:
        eq, dates, m, avg_turn, _ = results[name]
        emit(f"{name}")
        emit(f"  full: {bt.fmt(m)}   turnover {avg_turn*100:.0f}%/mo")
        mid = len(eq) // 2
        m1 = bt.metrics(eq[:mid + 1], dates[:mid + 1])
        m2 = bt.metrics(eq[mid:], dates[mid:])
        emit(f"  1st half: {bt.fmt(m1)}")
        emit(f"  2nd half: {bt.fmt(m2)}")
        emit("")
    emit(f"SPY B&H")
    emit(f"  full: {bt.fmt(m_b)}")
    mid = len(b_eq) // 2
    emit(f"  1st half: {bt.fmt(bt.metrics(b_eq[:mid+1], v1_dates[:mid+1]))}")
    emit(f"  2nd half: {bt.fmt(bt.metrics(b_eq[mid:], v1_dates[mid:]))}")

    # per-year, V1 + V2 vs SPY
    emit("\nPer-year returns (V1 / V2 / SPY):")
    lookup = {}
    for name in results:
        eq, dates, _, _, _ = results[name]
        lookup[name] = (eq, dates)
    by_year = {}
    for i, d in enumerate(v1_dates):
        by_year.setdefault(d[:4], []).append(i)
    v1n, v2n = variants[0][0], variants[1][0]
    for y in sorted(by_year):
        idx = by_year[y]
        if len(idx) < 2:
            continue
        def yr(eq):
            return eq[idx[-1]] / eq[idx[0]] - 1
        emit(f"  {y}: {yr(lookup[v1n][0])*100:7.2f}% / {yr(lookup[v2n][0])*100:7.2f}% / {yr(b_eq)*100:7.2f}%")

    # V2 diagnostics: how often invested?
    _, _, _, _, v2_picks = results[v2n]
    invested = [len(p) for _, p in v2_picks]
    emit(f"\nV2 diagnostics: avg positions {sum(invested)/len(invested):.1f}/5, "
         f"months fully in cash: {sum(1 for n in invested if n == 0)}/{len(invested)}")

    emit("\n" + "=" * 74)
    win = []
    for name in (v1n, v2n):
        m = results[name][2]
        eq, dates = lookup[name]
        mid = len(eq) // 2
        s1 = bt.metrics(eq[:mid + 1], dates[:mid + 1])["sharpe"]
        s2 = bt.metrics(eq[mid:], dates[mid:])["sharpe"]
        b1 = bt.metrics(b_eq[:mid + 1], v1_dates[:mid + 1])["sharpe"]
        b2 = bt.metrics(b_eq[mid:], v1_dates[mid:])["sharpe"]
        ok = m["sharpe"] > m_b["sharpe"] and s1 > b1 and s2 > b2
        win.append(ok)
        emit(f"{name}: {'BEATS SPY risk-adjusted in full AND both halves' if ok else 'FAILS the both-halves Sharpe bar'}")
    emit("Bar for 'proven': beat SPY Sharpe in full period AND both halves, net of costs.")
    emit("=" * 74)

    out = os.path.join(HERE, "backtest-feargreed-results.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Fear/Greed contrarian rotation results\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\nResults written to {out}")


if __name__ == "__main__":
    main()
