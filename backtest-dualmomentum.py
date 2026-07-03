#!/usr/bin/env python3
"""
backtest-dualmomentum.py — Antonacci GEM (Global Equities Momentum), the
PUBLISHED academic/practitioner rotation strategy, tested on our data as a
benchmark. Purpose: if even the best-known published rotation rule fails the
bar out-of-sample (2010-2026), the monthly-rotation question is closed.

PRE-REGISTERED RULES (from "Dual Momentum Investing", not tuned here):
  Monthly, using data through the previous close:
    r_spy = 12-month return of SPY, r_efa = 12-month return of EFA
    If max(r_spy, r_efa) > hurdle (0%):  hold the winner
    Else:                                hold IEF (bonds)
  Executed at the close of the first trading day of the month.
  Costs: 15 bps/side on switches. Hurdle: book uses T-bills; our cache has no
  T-bill series, so 0% is used — this makes the risk-off trigger slightly
  LAXER, which if anything flatters the strategy in the 2022+ rate era.

Pass bar (same as every other test): beat SPY on Sharpe net of costs in the
full period AND both halves.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("bt", os.path.join(HERE, "backtest-buyscore.py"))
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

LOOKBACK = 252   # ~12 months of trading days
HURDLE = 0.0
DEFENSIVE = "IEF"
RISK_ASSETS = ["SPY", "EFA"]
COST = bt.COST_BPS / 10000.0


def main():
    data = bt.load_data("--refresh" in sys.argv)
    for t in RISK_ASSETS + [DEFENSIVE]:
        if t not in data:
            print(f"missing {t}")
            sys.exit(1)

    calendar = bt.build_calendar(data)
    aligned = bt.align(data, calendar)
    rebs = [i for i in bt.month_starts(calendar) if i > 0]

    equity = [1.0]
    eq_dates = []
    held = None
    switches = 0
    months_in = {t: 0 for t in RISK_ASSETS + [DEFENSIVE]}
    log = []

    for k, r in enumerate(rebs):
        i = r - 1
        rets = {}
        for t in RISK_ASSETS:
            closes, first = aligned[t]
            if i - LOOKBACK >= first and closes[i] and closes[i - LOOKBACK]:
                rets[t] = closes[i] / closes[i - LOOKBACK] - 1
        if len(rets) < len(RISK_ASSETS):
            target = None  # not enough history yet: stay in cash
        else:
            best = max(rets, key=rets.get)
            target = best if rets[best] > HURDLE else DEFENSIVE
        if target != held:
            # full switch: sell old, buy new = 2 sides (or 1 side from/to cash)
            sides = (1 if held else 0) + (1 if target else 0)
            equity[-1] *= (1 - sides * COST)
            switches += 1 if held or target else 0
            held = target
        if held:
            months_in[held] += 1
        log.append((calendar[r], held or "CASH"))
        r_next = rebs[k + 1] if k + 1 < len(rebs) else len(calendar) - 1
        for j in range(r, r_next):
            if held:
                c0, c1 = aligned[held][0][j], aligned[held][0][j + 1]
                day = (c1 / c0 - 1) if (c0 and c1) else 0.0
            else:
                day = 0.0
            equity.append(equity[-1] * (1 + day))
            eq_dates.append(calendar[j + 1])

    all_dates = [calendar[rebs[0]]] + eq_dates
    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("=" * 74)
    emit(f"  Dual Momentum (GEM): SPY/EFA 12-mo relative + absolute momentum, IEF defensive")
    emit(f"  {all_dates[0]} -> {all_dates[-1]}, {bt.COST_BPS}bps/side, hurdle {HURDLE:.0%}")
    emit("=" * 74)
    m = bt.metrics(equity, all_dates)
    b_eq = bt.bench_equity(data, calendar, all_dates)
    m_b = bt.metrics(b_eq, all_dates)
    emit(f"\nGEM     (full): {bt.fmt(m)}")
    emit(f"SPY B&H (full): {bt.fmt(m_b)}")
    mid = len(equity) // 2
    for label, sl in (("1st half", slice(0, mid + 1)), ("2nd half", slice(mid, None))):
        emit(f"\n{label} GEM: {bt.fmt(bt.metrics(equity[sl], all_dates[sl]))}")
        emit(f"{label} SPY: {bt.fmt(bt.metrics(b_eq[sl], all_dates[sl]))}")

    total_months = sum(months_in.values())
    emit(f"\nAllocation: " + ", ".join(f"{t} {months_in[t]/max(1,total_months)*100:.0f}%" for t in months_in))
    emit(f"Switches: {switches} over {len(rebs)} months")

    emit("\nPer-year (GEM vs SPY):")
    by_year = {}
    for idx, d in enumerate(all_dates):
        by_year.setdefault(d[:4], []).append(idx)
    for y in sorted(by_year):
        ix = by_year[y]
        if len(ix) < 2:
            continue
        g = equity[ix[-1]] / equity[ix[0]] - 1
        s = b_eq[ix[-1]] / b_eq[ix[0]] - 1
        emit(f"  {y}: {g*100:7.2f}%  vs  {s*100:7.2f}%{'  <-- LAGS' if g < s else ''}")

    s1 = bt.metrics(equity[:mid + 1], all_dates[:mid + 1])["sharpe"]
    s2 = bt.metrics(equity[mid:], all_dates[mid:])["sharpe"]
    b1 = bt.metrics(b_eq[:mid + 1], all_dates[:mid + 1])["sharpe"]
    b2 = bt.metrics(b_eq[mid:], all_dates[mid:])["sharpe"]
    passed = m["sharpe"] > m_b["sharpe"] and s1 > b1 and s2 > b2
    emit("\n" + "=" * 74)
    emit(f"VERDICT: GEM {'PASSES' if passed else 'FAILS'} the bar "
         f"(Sharpe vs SPY — full: {m['sharpe']:.2f} vs {m_b['sharpe']:.2f}, "
         f"h1: {s1:.2f} vs {b1:.2f}, h2: {s2:.2f} vs {b2:.2f})")
    emit("This is the strongest published monthly-rotation rule. If it fails")
    emit("out-of-sample here, monthly ETF rotation is closed as a research line.")
    emit("=" * 74)

    out = os.path.join(HERE, "backtest-dualmomentum-results.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Dual Momentum (GEM) benchmark results\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\nResults written to {out}")


if __name__ == "__main__":
    main()
