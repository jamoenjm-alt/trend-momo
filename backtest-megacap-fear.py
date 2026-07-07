#!/usr/bin/env python3
"""
backtest-megacap-fear.py — "buy maximum fear in the top-10 market-cap stocks."

HYPOTHESIS (user's): the biggest, highest-quality companies bounce back from
fear, so buying the most beaten-down giants should outperform.

SURVIVORSHIP HANDLING: the top-10 list is POINT-IN-TIME per calendar year
(approximate, from public record — start-of-year membership). Using today's
top-10 across 2010-2026 would smuggle NVDA/TSLA hindsight into the test.
All names remained listed (mega caps rarely delist), so Yahoo data is usable.
FB history is under META. Residual bias is small but nonzero — noted.

PRE-REGISTERED VARIANTS (fixed before running; do not tune):
  V1  Fear rotation: each month hold the 3 LOWEST-Trend-Score names of that
      year's top-10, equal weight. Always invested.
  V2  Dip-buy: buy any top-10 name when its score <= 2 (up to 5 slots, most
      feared first); sell when score >= 7. Idle slots in cash at 0%.
  REF Equal-weight all 10 giants, monthly rebalance — THE benchmark that
      matters: if fear-timing can't beat the untimed basket, timing adds
      nothing. SPY buy-and-hold also shown.
Costs: 15 bps/side. Pass bar: beat BOTH SPY and the equal-weight basket on
Sharpe, net of costs, in the full period AND both halves.

Data cached in backtest-megacap-data.json. Results to
backtest-megacap-results.md.
"""

import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("bt", os.path.join(HERE, "backtest-buyscore.py"))
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

# Approximate point-in-time top-10 US market cap, start of each year (public record).
TOP10 = {
    2010: ["XOM", "MSFT", "AAPL", "WMT", "GOOGL", "JNJ", "PG", "IBM", "GE", "CVX"],
    2011: ["XOM", "AAPL", "MSFT", "IBM", "CVX", "WMT", "GE", "GOOGL", "JNJ", "PG"],
    2012: ["AAPL", "XOM", "MSFT", "IBM", "WMT", "GE", "CVX", "GOOGL", "JNJ", "PG"],
    2013: ["AAPL", "XOM", "GOOGL", "MSFT", "GE", "JNJ", "WMT", "CVX", "PG", "WFC"],
    2014: ["AAPL", "XOM", "MSFT", "GOOGL", "JNJ", "GE", "WFC", "WMT", "PG", "CVX"],
    2015: ["AAPL", "GOOGL", "MSFT", "XOM", "JNJ", "GE", "WFC", "AMZN", "META", "PG"],
    2016: ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "XOM", "JNJ", "JPM", "GE", "WFC"],
    2017: ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "BRK-B", "JNJ", "XOM", "JPM", "WFC"],
    2018: ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "BRK-B", "JPM", "JNJ", "XOM", "V"],
    2019: ["MSFT", "AAPL", "AMZN", "GOOGL", "META", "BRK-B", "JPM", "JNJ", "V", "XOM"],
    2020: ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "BRK-B", "V", "JNJ", "WMT", "JPM"],
    2021: ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "V", "JPM", "JNJ"],
    2022: ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "BRK-B", "NVDA", "JNJ", "V"],
    2023: ["AAPL", "MSFT", "GOOGL", "AMZN", "BRK-B", "NVDA", "TSLA", "XOM", "UNH", "JNJ"],
    2024: ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY", "TSLA", "V"],
    2025: ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "BRK-B", "TSLA", "AVGO", "LLY"],
    2026: ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "BRK-B", "TSLA", "AVGO", "LLY"],
}
ALL_TICKERS = sorted({t for lst in TOP10.values() for t in lst} | {"SPY"})
FEAR_N = 3          # V1: hold this many most-feared giants
DIP_ENTRY = 2.0     # V2 entry score
DIP_EXIT = 7.0      # V2 exit score
DIP_SLOTS = 5
COST = bt.COST_BPS / 10000.0
CACHE = os.path.join(HERE, "backtest-megacap-data.json")


def load_data(refresh=False):
    if not refresh and os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            data = json.load(f)
        if set(ALL_TICKERS) <= set(data):
            print(f"Using cached data ({CACHE})")
            return data
    data = {}
    print(f"Fetching {len(ALL_TICKERS)} tickers from Yahoo...")
    for s in ALL_TICKERS:
        print(f"  {s}...", end=" ", flush=True)
        d = bt.fetch_yahoo_daily(s)
        print(f"{len(d)} days")
        if d:
            data[s] = d
        time.sleep(0.4)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def run(data, select_fn, stateful=False):
    calendar = sorted(data["SPY"].keys())
    aligned = bt.align(data, calendar)
    rebs = [i for i in bt.month_starts(calendar) if i > 0]
    equity, eq_dates, holdings, turnover = [1.0], [], {}, 0.0
    for k, r in enumerate(rebs):
        year = int(calendar[r][:4])
        members = [t for t in TOP10.get(year, TOP10[max(TOP10)]) if t in data]
        scores = {}
        allsc = bt.scores_on(aligned, calendar, r - 1)
        for t in members:
            if t in allsc:
                scores[t] = allsc[t]
        new_w = select_fn(scores, dict(holdings))
        turn = sum(abs(new_w.get(t, 0) - holdings.get(t, 0)) for t in set(new_w) | set(holdings))
        turnover += turn
        equity[-1] *= (1 - turn * COST)
        holdings = new_w
        r_next = rebs[k + 1] if k + 1 < len(rebs) else len(calendar) - 1
        for i in range(r, r_next):
            day = 0.0
            for t, w in holdings.items():
                c0, c1 = aligned[t][0][i], aligned[t][0][i + 1]
                if c0 and c1:
                    day += w * (c1 / c0 - 1)
            equity.append(equity[-1] * (1 + day))
            eq_dates.append(calendar[i + 1])
    return calendar, equity, [calendar[rebs[0]]] + eq_dates, turnover / max(1, len(rebs))


def sel_fear(scores, _h):
    ranked = sorted(scores.items(), key=lambda kv: kv[1])[:FEAR_N]
    return {t: 1.0 / FEAR_N for t, _ in ranked}


def sel_dip(scores, holdings):
    kept = {t: 1.0 / DIP_SLOTS for t in holdings if scores.get(t, 10.0) < DIP_EXIT}
    free = DIP_SLOTS - len(kept)
    if free > 0:
        cands = sorted((s, t) for t, s in scores.items() if s <= DIP_ENTRY and t not in kept)
        for s, t in cands[:free]:
            kept[t] = 1.0 / DIP_SLOTS
    return kept


def sel_equal(scores, _h):
    if not scores:
        return {}
    return {t: 1.0 / len(scores) for t in scores}


def main():
    data = load_data("--refresh" in sys.argv)
    missing = [t for t in ALL_TICKERS if t not in data]
    if missing:
        print(f"WARNING: missing {missing}")
    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("=" * 74)
    emit("  Mega-cap fear backtest — point-in-time top-10 by market cap")
    emit(f"  {bt.COST_BPS}bps/side, monthly. Bar: beat SPY AND the equal-weight basket")
    emit("  on Sharpe in full period and both halves, net of costs.")
    emit("=" * 74)

    results = {}
    for name, fn in [
        (f"V1 fear rotation (hold {FEAR_N} most-feared giants)", sel_fear),
        (f"V2 dip-buy (enter <= {DIP_ENTRY:.0f}, exit >= {DIP_EXIT:.0f})", sel_dip),
        ("REF equal-weight all 10 giants (untimed)", sel_equal),
    ]:
        calendar, eq, dates, avg_turn = run(data, fn)
        results[name] = (eq, dates, avg_turn)

    ref_eq, ref_dates, _ = results["REF equal-weight all 10 giants (untimed)"]
    b_eq = bt.bench_equity(data, sorted(data["SPY"].keys()), ref_dates)

    def halves(eq, dates):
        mid = len(eq) // 2
        return (bt.metrics(eq, dates), bt.metrics(eq[:mid + 1], dates[:mid + 1]),
                bt.metrics(eq[mid:], dates[mid:]))

    mb_f, mb_1, mb_2 = halves(b_eq, ref_dates)
    for name in results:
        eq, dates, avg_turn = results[name]
        m_f, m_1, m_2 = halves(eq, dates)
        emit(f"\n{name}   (turnover {avg_turn*100:.0f}%/mo)")
        emit(f"  full:     {bt.fmt(m_f)}")
        emit(f"  1st half: {bt.fmt(m_1)}")
        emit(f"  2nd half: {bt.fmt(m_2)}")
    emit(f"\nSPY B&H")
    emit(f"  full:     {bt.fmt(mb_f)}")
    emit(f"  1st half: {bt.fmt(mb_1)}")
    emit(f"  2nd half: {bt.fmt(mb_2)}")

    emit("\nPer-year (V1 / V2 / EW-10 / SPY):")
    v1, v2 = list(results.values())[0][0], list(results.values())[1][0]
    by_year = {}
    for i, d in enumerate(ref_dates):
        by_year.setdefault(d[:4], []).append(i)
    for y in sorted(by_year):
        ix = by_year[y]
        if len(ix) < 2:
            continue
        def yr(eq):
            return (eq[ix[-1]] / eq[ix[0]] - 1) * 100
        emit(f"  {y}: {yr(v1):7.2f}% / {yr(v2):7.2f}% / {yr(ref_eq):7.2f}% / {yr(b_eq):7.2f}%")

    emit("\n" + "=" * 74)
    for name in list(results)[:2]:
        eq, dates, _ = results[name]
        m_f, m_1, m_2 = halves(eq, dates)
        rf, r1, r2 = halves(ref_eq, ref_dates)
        beats_spy = m_f["sharpe"] > mb_f["sharpe"] and m_1["sharpe"] > mb_1["sharpe"] and m_2["sharpe"] > mb_2["sharpe"]
        beats_ew = m_f["sharpe"] > rf["sharpe"] and m_1["sharpe"] > r1["sharpe"] and m_2["sharpe"] > r2["sharpe"]
        verdict = "PASSES the full bar" if (beats_spy and beats_ew) else \
                  ("beats SPY but NOT the untimed basket — timing added nothing" if beats_spy else "FAILS")
        emit(f"{name}: {verdict}")
    emit("Universe is point-in-time top-10 (approximate, public record); residual")
    emit("bias small but nonzero. Costs on. No parameters were tuned after running.")
    emit("=" * 74)

    out = os.path.join(HERE, "backtest-megacap-results.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Mega-cap fear backtest\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\nResults written to {out}")


if __name__ == "__main__":
    main()
