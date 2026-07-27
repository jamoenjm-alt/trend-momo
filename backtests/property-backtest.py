"""
property-backtest.py — Did the board's buy/sell screen actually work?
═════════════════════════════════════════════════════════════════════

Walk forward one month at a time over the last N years. At each month-end,
rebuild the buy/sell score using ONLY data that existed on that date, take the
top-ranked market, then measure what its asking-price index actually did over
the following 6 / 12 / 24 months. Compare against a benchmark so we're
measuring skill, not just the Australian property market going up.

Reads data/property-history.json (written by update-property.py — full
untrimmed series). Writes backtests/property-picks-history.json.

    python backtests/property-backtest.py            # 3 years (default)
    python backtests/property-backtest.py --years 5

NO LOOK-AHEAD. Every input is truncated to the as-of date before scoring:
  - price index      weekly, truncated
  - rent             weekly, truncated
  - rental yield     weekly, truncated (percentile computed vs history to date)
  - vacancy          monthly, truncated
  - stock on market  monthly, truncated
The one unavoidable bias is region selection: the 420-market list was chosen
today. Property markets don't delist, so this is mild, but it is not zero.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HIST = os.path.join(ROOT, "data", "property-history.json")
OUT = os.path.join(HERE, "property-picks-history.json")

# Must mirror property-board.html scorePicks() exactly.
MA_PAIRS = [(12, 4, "h1"), (18, 6, "h1"), (26, 9, "h1"),
            (33, 11, "h2"), (39, 13, "h2"), (52, 17, "h2"),
            (65, 22, "h3"), (78, 26, "h3"), (104, 35, "h3"),
            (130, 43, "h4"), (195, 65, "h4"), (260, 87, "h4")]
GROUPS = ["h1", "h2", "h3", "h4"]
MIN_LISTINGS = 100
MIN_WEEKS = 260


def sma(seq, w):
    return sum(seq[-w:]) / w if len(seq) >= w else None


def signals(px):
    if len(px) < 30:
        return None
    price = px[-1]
    mas = {}
    for n in {p for pair in MA_PAIRS for p in pair[:2]}:
        if len(px) >= n:
            mas[n] = sma(px, n)
    per_group = {g: [] for g in GROUPS}
    for slow, fast, g in MA_PAIRS:
        s, f = mas.get(slow), mas.get(fast)
        if s is not None:
            per_group[g].append(1 if price > s else -1)
        if s is not None and f is not None:
            per_group[g].append(1 if f > s else -1)
    cols = {g: (sum(v) / len(v) if v else None) for g, v in per_group.items()}
    allv = [x for v in per_group.values() for x in v]
    return {"cols": cols, "all": sum(allv) / len(allv) if allv else None}


def cl01(x, lo, hi):
    if x is None:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def pct_rank(vals, x):
    vals = [v for v in vals if v is not None]
    if not vals or x is None:
        return None
    return 100.0 * sum(1 for v in vals if v <= x) / len(vals)


def upto(series, asof):
    """series is [[date_or_month, value], ...]; keep entries <= asof."""
    return [v for d, v in series if d <= asof]


def max_drawdown(px):
    peak, worst = px[0], 0.0
    for v in px:
        peak = max(peak, v)
        if peak:
            worst = min(worst, v / peak - 1)
    return worst * 100


def score_asof(regions, asof_date, asof_month):
    rows = []
    for code, r in regions.items():
        if r.get("state") == "NAT":
            continue
        px = upto(r.get("px") or [], asof_date)
        if len(px) < MIN_WEEKS:
            continue
        stock_s = upto(r.get("stock") or [], asof_month)
        if len(stock_s) < 13 or stock_s[-1] < MIN_LISTINGS:
            continue
        yld_s = upto(r.get("yield") or [], asof_date)
        vac_s = upto(r.get("vac") or [], asof_month)
        rent_s = upto(r.get("rent") or [], asof_date)
        if not yld_s or not vac_s or len(rent_s) < 53:
            continue

        s = signals(px)
        if not s or s["all"] is None:
            continue
        yld = yld_s[-1]
        ypc = pct_rank(yld_s, yld)
        vac = vac_s[-1]
        vac12 = vac_s[-13] if len(vac_s) >= 13 else vac
        stock, stock12 = stock_s[-1], stock_s[-13]
        rent, rent52 = rent_s[-1], rent_s[-53]
        dd = (px[-1] / max(px) - 1) * 100
        ddmax = max_drawdown(px)
        rentg = (rent / rent52 - 1) * 100 if rent52 else 0.0
        stockg = (stock / stock12 - 1) * 100 if stock12 else 0.0
        vacd = vac - vac12
        h1 = s["cols"].get("h1") or 0.0
        h4 = s["cols"].get("h4") or 0.0

        risk = 1 - (cl01(-ddmax, 15, 45) * 0.30 + cl01(300 - stock, 0, 200) * 0.10)
        buy = (0.20 * (ypc / 100) + 0.10 * cl01(yld, 2.5, 5.5) + 0.12 * cl01(-dd, 0, 15)
               + 0.20 * cl01(2.5 - vac, 0, 2.0) + 0.20 * cl01(rentg, 0, 10)
               + 0.10 * cl01(-stockg, 0, 20)
               + 0.08 * (cl01((h4 + 1) / 2, 0, 1) * (1 - cl01((h1 + 1) / 2, 0, 1) * 0.5))) * risk
        sell = (0.22 * (1 - ypc / 100) + 0.12 * cl01(dd, -5, 0)
                + 0.20 * (cl01(vac, 1.0, 3.0) * 0.6 + cl01(vacd, 0, 0.8) * 0.4)
                + 0.20 * cl01(3 - rentg, 0, 8) + 0.16 * cl01(stockg, 0, 25)
                + 0.10 * (cl01((h4 + 1) / 2, 0, 1) * (1 - cl01((h1 + 1) / 2, 0, 1))))
        rows.append({"code": code, "name": r["name"], "state": r["state"],
                     "buy": buy, "sell": sell, "px_at": px[-1],
                     "yield": yld, "ypc": ypc, "vac": vac,
                     "rentg": rentg, "stockg": stockg, "dd": dd, "stock": stock})
    return rows


def px_at(series, date_str):
    vals = upto(series, date_str)
    return vals[-1] if vals else None


def fwd(series, start, months):
    """% change in the index from `start` to `start + months`."""
    a = px_at(series, start)
    d = datetime.strptime(start, "%Y-%m-%d") + timedelta(days=int(months * 30.44))
    end = d.strftime("%Y-%m-%d")
    last_date = series[-1][0] if series else None
    if last_date is None or end > last_date:
        return None
    b = px_at(series, end)
    if not a or not b:
        return None
    return (b / a - 1) * 100


def main():
    years = 3
    if "--years" in sys.argv:
        years = int(sys.argv[sys.argv.index("--years") + 1])

    with open(HIST, encoding="utf-8") as f:
        data = json.load(f)
    regions = data["regions"]
    print(f"loaded {len(regions)} regions, baked {data.get('updated')}")

    # month-end dates going back `years`
    today = datetime.now(timezone.utc)
    months = []
    y, m = today.year, today.month
    for _ in range(years * 12):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        last_day = (datetime(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
        months.append(datetime(y, m, last_day))
    months.reverse()

    bench = regions.get("CAP8", {}).get("px") or regions.get("AUS", {}).get("px") or []

    results = []
    for dt in months:
        asof = dt.strftime("%Y-%m-%d")
        asof_m = dt.strftime("%Y-%m")
        rows = score_asof(regions, asof, asof_m)
        if not rows:
            continue
        top_buy = max(rows, key=lambda r: r["buy"])
        top_sell = max(rows, key=lambda r: r["sell"])
        med_buy = sorted(r["buy"] for r in rows)[len(rows) // 2]

        rec = {"asof": asof, "eligible": len(rows), "median_buy_score": round(med_buy, 3)}
        for side, pick in (("buy", top_buy), ("sell", top_sell)):
            px = regions[pick["code"]]["px"]
            rec[side] = {
                "code": pick["code"], "name": pick["name"], "state": pick["state"],
                "score": round(pick[side], 3),
                "yield": pick["yield"], "yield_pctile": round(pick["ypc"], 1),
                "vacancy": pick["vac"], "rent_12m": round(pick["rentg"], 1),
                "listings_12m": round(pick["stockg"], 1), "listings": pick["stock"],
                "fwd_6m": fwd(px, asof, 6), "fwd_12m": fwd(px, asof, 12),
                "fwd_24m": fwd(px, asof, 24),
            }
        for hz in (6, 12, 24):
            rec[f"bench_{hz}m"] = fwd(bench, asof, hz)
            # median forward return of every eligible market that month
            fs = [fwd(regions[r["code"]]["px"], asof, hz) for r in rows]
            fs = sorted(x for x in fs if x is not None)
            rec[f"universe_median_{hz}m"] = fs[len(fs) // 2] if fs else None
        results.append(rec)
        b, s = rec["buy"], rec["sell"]
        f6 = lambda v: "   n/a" if v is None else f"{v:+6.1f}%"
        print(f"{asof}  BUY {b['name'][:20]:20} {f6(b['fwd_12m'])} 12m   |  "
              f"SELL {s['name'][:20]:20} {f6(s['fwd_12m'])} 12m   "
              f"(bench {f6(rec['bench_12m'])})")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"generated": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "years": years, "months": results}, f, indent=1)
    print(f"\nwrote {OUT} ({len(results)} months)")

    # ── Summary ──────────────────────────────────────────────────────────
    def summarise(side, hz):
        key = f"fwd_{hz}m"
        pairs = [(r[side][key], r[f"universe_median_{hz}m"], r[f"bench_{hz}m"])
                 for r in results if r[side][key] is not None
                 and r[f"universe_median_{hz}m"] is not None]
        if not pairs:
            return None
        picks = [p[0] for p in pairs]
        univ = [p[1] for p in pairs]
        benc = [p[2] for p in pairs if p[2] is not None]
        excess = [p[0] - p[1] for p in pairs]
        return {"n": len(pairs), "pick": sum(picks) / len(picks),
                "universe": sum(univ) / len(univ),
                "bench": sum(benc) / len(benc) if benc else None,
                "excess": sum(excess) / len(excess),
                "beat_rate": 100.0 * sum(1 for e in excess if e > 0) / len(excess)}

    print("\n" + "=" * 78)
    print("RESULT — average forward change in the picked market's asking index")
    print("=" * 78)
    for side in ("buy", "sell"):
        print(f"\n{side.upper()} picks:")
        print(f"  {'horizon':8} {'n':>3} {'pick':>9} {'all mkts':>9} "
              f"{'capital8':>9} {'excess':>9} {'beat %':>7}")
        for hz in (6, 12, 24):
            r = summarise(side, hz)
            if not r:
                print(f"  {str(hz)+'m':8} {'—':>3}  (not enough forward data yet)")
                continue
            bs = f"{r['bench']:+8.1f}%" if r["bench"] is not None else "     n/a"
            print(f"  {str(hz)+'m':8} {r['n']:>3} {r['pick']:+8.1f}% "
                  f"{r['universe']:+8.1f}% {bs} {r['excess']:+8.1f}% {r['beat_rate']:6.0f}%")
    print("\n'excess' = pick minus the median of every eligible market that month.")
    print("That is the only number that says whether the screen adds anything.")


if __name__ == "__main__":
    main()
