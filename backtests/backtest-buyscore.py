#!/usr/bin/env python3
"""
backtest-buyscore.py — walk-forward, point-in-time backtest of the board's buyScore
on a survivorship-bias-FREE ETF universe, net of costs, vs SPY buy-and-hold.

WHY ETFs: every stock-level backtest on Yahoo data is survivorship-biased (only
names that survived to today). ETFs don't have that problem — sector SPDRs, broad
index, bond and gold ETFs have existed continuously. Results here are honest.
When you get bias-free stock data (Norgate/CRSP), point UNIVERSE at it.

WHAT IT TESTS
  1. Signal validity: at every monthly rebalance, rank the universe by buyScore
     and measure forward 21-trading-day returns per score bucket. If buyScore has
     an edge, higher buckets should earn more (monotonicity) OUT of sample.
  2. Strategy: hold the TOP_N tickers with buyScore >= MIN_SCORE, equal weight,
     monthly rebalance, remainder in cash (0% yield — deliberately conservative).
     Costs: COST_BPS per side on turnover. Executed at the close of the first
     trading day of the month using signals computed through the PREVIOUS close
     (no lookahead).
  3. Walk-forward: metrics reported for full period, first half, second half,
     and per-year. A strategy that only works in one half is regime luck.

HONESTY RULES (do not weaken these):
  - Signals only ever see data up to the day BEFORE execution.
  - Costs and cash drag stay on. If it only wins with zero costs, it loses.
  - The benchmark is investable SPY total price return, same calendar.
  - Do not tune parameters until they "work" — that is in-sample overfitting.
    If you must explore, split: tune on 2010-2017, validate untouched 2018+.

USAGE
  python backtest-buyscore.py            # fetch (or use cache) and run
  python backtest-buyscore.py --refresh  # force re-download of price data

Data is cached in backtest-etf-data.json next to this script, so subsequent
runs are offline. Results are written to backtest-buyscore-results.md.
"""

import json
import math
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

# ── Parameters ───────────────────────────────────────────────────────────────
TOP_N      = 5      # hold this many tickers max
MIN_SCORE  = 5.0    # only hold names scoring at least this (5 = neutral)
COST_BPS   = 15     # per-side cost in basis points (commission + slippage)
START      = "2010-01-01"
FWD_DAYS   = 21     # forward-return horizon for the signal-validity test

# Bias-free, liquid, long-history ETF universe. SPY included: the strategy is
# allowed to just own the benchmark if that's what the signal says.
UNIVERSE = [
    "SPY", "QQQ", "DIA", "IWM",                                  # US broad
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLU", "XLY", "XLB",  # sectors
    "EFA", "EEM", "EWJ", "FXI",                                  # international
    "TLT", "IEF", "HYG", "LQD",                                  # bonds
    "GLD", "SLV",                                                # metals
]
BENCHMARK = "SPY"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest-etf-data.json")

# ── Yahoo fetch (same endpoint update-prices.py uses) ────────────────────────
def fetch_yahoo_daily(symbol, start=START, retries=3):
    end = int(datetime.now(timezone.utc).timestamp())
    p1 = int(datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?interval=1d&period1={p1}&period2={end}&events=history")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    for attempt in range(retries):
        if attempt:
            time.sleep(2 ** attempt)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = json.loads(r.read().decode("utf-8"))
            res = raw["chart"]["result"][0]
            ts = res["timestamp"]
            cl = res["indicators"]["quote"][0]["close"]
            # Use adjusted close when available (dividends matter over 15y).
            adj = None
            try:
                adj = res["indicators"]["adjclose"][0]["adjclose"]
            except (KeyError, IndexError, TypeError):
                pass
            src = adj if adj else cl
            out = {}
            for t, c in zip(ts, src):
                if c is not None:
                    out[datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")] = round(float(c), 6)
            return out
        except Exception as e:
            if attempt == retries - 1:
                print(f"  {symbol}: FAILED ({e})")
    return {}

def load_data(refresh=False):
    if not refresh and os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            data = json.load(f)
        if set(UNIVERSE) <= set(data):
            print(f"Using cached data ({CACHE})")
            return data
    data = {}
    print(f"Fetching {len(UNIVERSE)} ETFs from Yahoo (~30s)...")
    for s in UNIVERSE:
        print(f"  {s}...", end=" ", flush=True)
        d = fetch_yahoo_daily(s)
        print(f"{len(d)} days")
        if d:
            data[s] = d
        time.sleep(0.4)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data

# ── buyScore math — EXACT port of regime-board.html (verified against the JS) ─
MA_PAIRS = [
    (10, 3, "canary"), (15, 5, "canary"),
    (42, 10, "st"), (50, 15, "st"), (63, 21, "st"),
    (84, 21, "lt"), (126, 42, "lt"), (168, 42, "lt"),
    (200, 50, "all"), (252, 63, "all"),
]
PERIODS = sorted({n for p in MA_PAIRS for n in p[:2]})

def prefix_sums(closes):
    pref = [0.0]
    for c in closes:
        pref.append(pref[-1] + c)
    return pref

def sma_at(pref, i, w):
    """SMA of window w ending at index i (inclusive). None if not enough data."""
    if i + 1 < w:
        return None
    return (pref[i + 1] - pref[i + 1 - w]) / w

def compute_signals_at(closes, pref, i):
    """Port of computeSignals(closes[0..i])."""
    price = closes[i]
    mas = {n: sma_at(pref, i, n) for n in PERIODS if i + 1 >= n}
    pair_sigs = []
    for slow, fast, group in MA_PAIRS:
        slow_ma = mas.get(slow)
        fast_ma = mas.get(fast)
        trend = (1 if price > slow_ma else -1) if slow_ma is not None else None
        momo = (1 if fast_ma > slow_ma else -1) if (fast_ma is not None and slow_ma is not None) else None
        pair_sigs.append((group, trend, momo))
    def col_avg(groups):
        vals = [s for g, t, m in pair_sigs if g in groups for s in (t, m) if s is not None]
        return sum(vals) / len(vals) if vals else None
    return {
        "canary": col_avg(("canary",)),
        "stTrend": col_avg(("st",)),
        "ltTrend": col_avg(("lt",)),
        "allInd": col_avg(("canary", "st", "lt", "all")),
    }

def regime_key(score):
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return "NO_DATA"
    if score > 0.6:
        return "STRONG_BULL"
    if score > 0.2:
        return "WEAK_BULL"
    if score > -0.2:
        return "SIDEWAYS"
    if score > -0.6:
        return "WEAK_BEAR"
    return "STRONG_BEAR"

def stability_at(closes, pref, i):
    """Port of computeStabilityState(closes[0..i])."""
    if i + 1 < 32:
        return "stable"
    def regime(lookback):
        j = i - lookback
        if j + 1 < 21:
            return None
        return regime_key(compute_signals_at(closes, pref, j)["allInd"])
    r0 = regime(0)
    if not r0 or r0 == "NO_DATA":
        return "stable"
    seq = [r for r in (regime(30), regime(20), regime(10), r0) if r]
    flips = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    if flips == 0:
        return "very_stable"
    if flips >= 2:
        return "very_unstable"
    r10 = regime(10)
    if r10 and r0 != r10:
        return "unstable"
    return "stable"

def buy_score_at(closes, pref, i):
    """Port of buyScore({...computeSignals, stability})."""
    sigs = compute_signals_at(closes, pref, i)
    weighted = ((sigs["canary"], 1), (sigs["stTrend"], 2), (sigs["ltTrend"], 3), (sigs["allInd"], 4))
    wsum = wtot = 0.0
    for v, w in weighted:
        if v is not None:
            wsum += v * w
            wtot += w
    if not wtot:
        return None
    base = (wsum / wtot + 1) / 2 * 9
    stab = stability_at(closes, pref, i)
    bonus = {"very_stable": 1, "stable": 0.5, "unstable": -0.5}.get(stab, -1)
    return min(10.0, max(0.0, base + bonus))

# ── Backtest engine ──────────────────────────────────────────────────────────
def build_calendar(data):
    """Trading calendar = benchmark's dates."""
    return sorted(data[BENCHMARK].keys())

def align(data, calendar):
    """ticker -> (closes list aligned to calendar with None gaps, first_idx)."""
    out = {}
    for t, series in data.items():
        closes, first = [], None
        for i, d in enumerate(calendar):
            v = series.get(d)
            if v is not None and first is None:
                first = i
            closes.append(v)
        # forward-fill interior gaps only (after inception)
        if first is not None:
            last = None
            for i in range(first, len(closes)):
                if closes[i] is None:
                    closes[i] = last
                else:
                    last = closes[i]
        out[t] = (closes, first if first is not None else len(calendar))
    return out

def month_starts(calendar):
    idx = []
    prev = None
    for i, d in enumerate(calendar):
        m = d[:7]
        if m != prev:
            idx.append(i)
            prev = m
    return idx

def scores_on(aligned, calendar, i_signal, min_history=260):
    """buyScore per ticker using data up to and including i_signal (prev close)."""
    out = {}
    for t, (closes, first) in aligned.items():
        n = i_signal - first + 1
        if n < min_history:
            continue
        window = [c for c in closes[first:i_signal + 1] if c is not None]
        if len(window) < min_history:
            continue
        pref = prefix_sums(window)
        s = buy_score_at(window, pref, len(window) - 1)
        if s is not None:
            out[t] = s
    return out

def run_backtest(data):
    calendar = build_calendar(data)
    aligned = align(data, calendar)
    rebs = [i for i in month_starts(calendar) if i > 0]
    cost = COST_BPS / 10000.0

    equity = [1.0]
    eq_dates = []
    holdings = {}          # ticker -> weight
    picks_log = []
    bucket_fwd = {}        # score bucket -> list of forward returns
    turnover_total = 0.0

    for k, r in enumerate(rebs):
        i_sig = r - 1
        scores = scores_on(aligned, calendar, i_sig)
        # signal-validity: forward FWD_DAYS return per score bucket (integer floor)
        if r + FWD_DAYS < len(calendar):
            for t, s in scores.items():
                c0 = aligned[t][0][r]
                c1 = aligned[t][0][r + FWD_DAYS]
                if c0 and c1:
                    bucket_fwd.setdefault(int(s), []).append(c1 / c0 - 1)
        # selection
        eligible = sorted(((s, t) for t, s in scores.items() if s >= MIN_SCORE), reverse=True)
        picks = [t for _, t in eligible[:TOP_N]]
        new_w = {t: 1.0 / TOP_N for t in picks}   # unfilled slots stay in cash
        # turnover cost
        tickers = set(new_w) | set(holdings)
        turn = sum(abs(new_w.get(t, 0) - holdings.get(t, 0)) for t in tickers)
        turnover_total += turn
        equity[-1] *= (1 - turn * cost)
        picks_log.append((calendar[r], picks))
        holdings = new_w
        # accrue returns until next rebalance (or end)
        r_next = rebs[k + 1] if k + 1 < len(rebs) else len(calendar) - 1
        for i in range(r, r_next):
            day_ret = 0.0
            for t, w in holdings.items():
                c0, c1 = aligned[t][0][i], aligned[t][0][i + 1]
                if c0 and c1:
                    day_ret += w * (c1 / c0 - 1)
            equity.append(equity[-1] * (1 + day_ret))
            eq_dates.append(calendar[i + 1])
    return calendar, equity, eq_dates, picks_log, bucket_fwd, turnover_total, rebs

# ── Metrics ──────────────────────────────────────────────────────────────────
def metrics(equity, dates):
    if len(equity) < 3:
        return None
    yrs = (datetime.strptime(dates[-1], "%Y-%m-%d") - datetime.strptime(dates[0], "%Y-%m-%d")).days / 365.25
    cagr = (equity[-1] / equity[0]) ** (1 / yrs) - 1 if yrs > 0 else 0
    rets = [equity[i + 1] / equity[i] - 1 for i in range(len(equity) - 1)]
    mu = sum(rets) / len(rets)
    var = sum((x - mu) ** 2 for x in rets) / (len(rets) - 1)
    vol = math.sqrt(var) * math.sqrt(252)
    sharpe = (mu * 252) / vol if vol > 0 else 0
    peak, maxdd = equity[0], 0.0
    for v in equity:
        peak = max(peak, v)
        maxdd = min(maxdd, v / peak - 1)
    return {"cagr": cagr, "vol": vol, "sharpe": sharpe, "maxdd": maxdd, "years": yrs}

def bench_equity(data, calendar, dates):
    ser = data[BENCHMARK]
    closes = [ser.get(d) for d in calendar]
    # align to strategy equity dates
    lookup = dict(zip(calendar, closes))
    eq, base = [], None
    for d in dates:
        c = lookup.get(d)
        if c:
            if base is None:
                base = c
            eq.append(c / base)
    return eq

def fmt(m):
    return (f"CAGR {m['cagr']*100:6.2f}%  vol {m['vol']*100:5.1f}%  "
            f"Sharpe {m['sharpe']:5.2f}  maxDD {m['maxdd']*100:6.1f}%")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    refresh = "--refresh" in sys.argv
    data = load_data(refresh)
    missing = [t for t in UNIVERSE if t not in data]
    if BENCHMARK not in data:
        print("No benchmark data — cannot proceed.")
        sys.exit(1)
    if missing:
        print(f"WARNING: missing {missing} — continuing without them.")

    calendar, equity, eq_dates, picks_log, bucket_fwd, turnover, rebs = run_backtest(data)
    all_dates = [calendar[rebs[0]]] + eq_dates

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("=" * 74)
    emit(f"  buyScore walk-forward backtest — {len(data)} ETFs, {all_dates[0]} → {all_dates[-1]}")
    emit(f"  top {TOP_N}, min score {MIN_SCORE}, {COST_BPS}bps/side, monthly rebalance, cash yields 0%")
    emit("=" * 74)

    m_full = metrics(equity, all_dates)
    b_eq = bench_equity(data, calendar, all_dates)
    m_bench = metrics(b_eq, all_dates)
    emit(f"\nStrategy (full): {fmt(m_full)}")
    emit(f"SPY B&H  (full): {fmt(m_bench)}")
    emit(f"Avg monthly turnover: {turnover / max(1, len(rebs)) * 100:.0f}%  "
         f"(≈{turnover / max(1, len(rebs)) * COST_BPS / 100 * 12:.2f}%/yr in costs)")

    # halves
    mid = len(equity) // 2
    for label, sl in (("1st half", slice(0, mid + 1)), ("2nd half", slice(mid, None))):
        ms = metrics(equity[sl], all_dates[sl])
        mb = metrics(b_eq[sl], all_dates[sl])
        emit(f"\n{label}  strategy: {fmt(ms)}")
        emit(f"{label}  SPY B&H : {fmt(mb)}")

    # per-year
    emit("\nPer-year (strategy vs SPY):")
    by_year = {}
    for i, d in enumerate(all_dates):
        by_year.setdefault(d[:4], []).append(i)
    for y in sorted(by_year):
        idx = by_year[y]
        if len(idx) < 2:
            continue
        s_ret = equity[idx[-1]] / equity[idx[0]] - 1
        b_ret = b_eq[idx[-1]] / b_eq[idx[0]] - 1
        flag = "  <-- LAGS" if s_ret < b_ret else ""
        emit(f"  {y}: {s_ret*100:7.2f}%  vs  {b_ret*100:7.2f}%{flag}")

    # signal validity
    emit(f"\nSignal validity: mean forward {FWD_DAYS}-day return by buyScore bucket")
    emit("(if buyScore works, higher buckets should earn more — monotonically)")
    keys = sorted(bucket_fwd)
    prev_mean = None
    breaks = 0
    for kb in keys:
        v = bucket_fwd[kb]
        mean = sum(v) / len(v)
        mono = ""
        if prev_mean is not None and mean < prev_mean:
            breaks += 1
            mono = "  (breaks monotonicity)"
        prev_mean = mean
        emit(f"  score {kb}-{kb+1}: {mean*100:6.2f}%   n={len(v)}{mono}")
    emit(f"Monotonicity breaks: {breaks} of {max(0, len(keys)-1)} steps")

    # verdict
    emit("\n" + "=" * 74)
    beat_cagr = m_full["cagr"] > m_bench["cagr"]
    beat_sharpe = m_full["sharpe"] > m_bench["sharpe"]
    emit(f"VERDICT: strategy {'BEATS' if beat_cagr else 'LOSES TO'} SPY on CAGR, "
         f"{'BEATS' if beat_sharpe else 'LOSES TO'} SPY on Sharpe, net of costs.")
    emit("A strategy is only 'proven' if it wins on Sharpe in BOTH halves.")
    emit("Remember: this is ETF-universe only. Stock-level claims still need")
    emit("survivorship-bias-free data (Norgate/CRSP).")
    emit("=" * 74)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest-buyscore-results.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# buyScore backtest results\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\nResults written to {out}")

    # recent picks for eyeballing
    print("\nLast 6 rebalances:")
    for d, picks in picks_log[-6:]:
        print(f"  {d}: {', '.join(picks) if picks else 'ALL CASH'}")

if __name__ == "__main__":
    main()
