"""
property-decile-validation.py — Is the property buy-score a real cross-sectional
signal, or a single-regime bet? Full-window decile validation.
══════════════════════════════════════════════════════════════════════════════

Added 2026-11-13 after the top-1 picks readout (property-picks-history.json)
was shown to be 26/36 WA over a 3-year window that was almost exactly the WA
boom — one macro call counted 36 times. This script asks the question properly:

  * every month since 2014, rank EVERY eligible market by buy score
  * bucket into deciles, measure forward excess over that month's universe median
  * is the decile curve monotone?  does it hold in every era?  does it survive
    removing the state bet?  which factor is actually doing the work?

Reads  data/property-history.json   (full untrimmed series, baked by update-property.py)
Writes backtests/property-decile-results.json   (small; safe to commit)

    python backtests/property-decile-validation.py              # 2014-07 → latest
    python backtests/property-decile-validation.py --start 2016-01

FORMULA INTEGRITY: the scoring here is a fast prefix-sum re-implementation of
property-backtest.score_asof(). Every run cross-checks it against the original
on sample months and ABORTS if any score differs by more than 1e-9. If you change
scorePicks() in the board, change property-backtest.py, and this check will tell
you whether this file still matches.

Results as at 2026-11-13 (history baked 2026-07-28, 138 months):
  decile spread D9-D0 : +6.7pp 6m · +11.2pp 12m · +19.5pp 24m · +26.9pp 36m, 9/9 monotone
  every era positive  : Sydney boom, 2017-19 downturn, COVID, rate shock, WA run
  state-neutral keeps : 81% (6m) · 71% (12m) · 60% (24m) of the edge
  driver              : vacancy (+16.5pp/24m alone), yield %ile, listings, rent growth
  NOT the driver      : price momentum — trailing 12m momentum is NEGATIVE (-3.9pp)
"""
import json, os, sys, bisect, math, statistics as st
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HIST = os.path.join(ROOT, "data", "property-history.json")
OUT  = os.path.join(HERE, "property-decile-results.json")
sys.path.insert(0, HERE)
import importlib
_orig = importlib.import_module("property-backtest")       # the canonical formula

MA_PAIRS = _orig.MA_PAIRS; GROUPS = _orig.GROUPS
MIN_LISTINGS = _orig.MIN_LISTINGS; MIN_WEEKS = _orig.MIN_WEEKS
cl01 = _orig.cl01; pct_rank = _orig.pct_rank
HORIZONS = (6, 12, 24, 36)
PINNED = ["TOM", "SEA", "ARD", "NRA", "ULL", "WOL", "BAY", "GOS"]   # markets to always report
ERAS = [("2014-08", "2017-07", "Sydney boom"), ("2017-08", "2020-03", "2017-19 downturn"),
        ("2020-04", "2022-04", "COVID boom"), ("2022-05", "2023-12", "Rate shock"),
        ("2024-01", "2099-12", "WA run / east fall")]

class Ser:
    __slots__ = ("d", "v", "cs")
    def __init__(self, pairs):
        self.d = [p[0] for p in pairs]; self.v = [p[1] for p in pairs]
        cs = [0.0]
        for x in self.v: cs.append(cs[-1] + (x if x is not None else 0.0))
        self.cs = cs
    def idx(self, asof): return bisect.bisect_right(self.d, asof)
    def sma(self, n, k): return (self.cs[k] - self.cs[k - n]) / n if k >= n else None

def load():
    data = json.load(open(HIST, encoding="utf-8"))
    regs = {}
    for code, r in data["regions"].items():
        px = r.get("px") or []
        if not px: continue
        P = Ser(px); rmax = []; rdd = []; peak = None; worst = 0.0
        for x in P.v:
            peak = x if peak is None or x > peak else peak
            rmax.append(peak)
            if peak: worst = min(worst, x / peak - 1)
            rdd.append(worst)
        regs[code] = {"name": r.get("name", code), "state": r.get("state"), "rmax": rmax, "rdd": rdd,
                      "px": P, "yield": Ser(r.get("yield") or []), "rent": Ser(r.get("rent") or []),
                      "vac": Ser(r.get("vac") or []), "stock": Ser(r.get("stock") or [])}
    return regs, data["regions"], data.get("updated")

def score_asof_fast(regs, asof, asof_m):
    rows = []
    for code, r in regs.items():
        if r["state"] == "NAT": continue
        P = r["px"]; k = P.idx(asof)
        if k < MIN_WEEKS: continue
        S = r["stock"]; ks = S.idx(asof_m)
        if ks < 13 or S.v[ks - 1] < MIN_LISTINGS: continue
        Y = r["yield"]; ky = Y.idx(asof); V = r["vac"]; kv = V.idx(asof_m); R = r["rent"]; kr = R.idx(asof)
        if ky < 1 or kv < 1 or kr < 53: continue
        price = P.v[k - 1]; mas = {}
        for n in {p for pr in MA_PAIRS for p in pr[:2]}:
            m = P.sma(n, k)
            if m is not None: mas[n] = m
        per = {g: [] for g in GROUPS}
        for slow, fast, g in MA_PAIRS:
            s, f = mas.get(slow), mas.get(fast)
            if s is not None: per[g].append(1 if price > s else -1)
            if s is not None and f is not None: per[g].append(1 if f > s else -1)
        cols = {g: (sum(v) / len(v) if v else None) for g, v in per.items()}
        if not [x for v in per.values() for x in v]: continue
        yld = Y.v[ky - 1]; ypc = pct_rank(Y.v[:ky], yld)
        vac = V.v[kv - 1]; vac12 = V.v[kv - 13] if kv >= 13 else vac
        stock = S.v[ks - 1]; stock12 = S.v[ks - 13]
        rent = R.v[kr - 1]; rent52 = R.v[kr - 53]
        dd = (price / r["rmax"][k - 1] - 1) * 100; ddmax = r["rdd"][k - 1] * 100
        rentg = (rent / rent52 - 1) * 100 if rent52 else 0.0
        stockg = (stock / stock12 - 1) * 100 if stock12 else 0.0
        vacd = vac - vac12
        h1 = cols.get("h1") or 0.0; h4 = cols.get("h4") or 0.0
        risk = 1 - (cl01(-ddmax, 15, 45) * 0.30 + cl01(300 - stock, 0, 200) * 0.10)
        buy = (0.20 * (ypc / 100) + 0.10 * cl01(yld, 2.5, 5.5) + 0.12 * cl01(-dd, 0, 15)
               + 0.20 * cl01(2.5 - vac, 0, 2.0) + 0.20 * cl01(rentg, 0, 10) + 0.10 * cl01(-stockg, 0, 20)
               + 0.08 * (cl01((h4 + 1) / 2, 0, 1) * (1 - cl01((h1 + 1) / 2, 0, 1) * 0.5))) * risk
        sell = (0.22 * (1 - ypc / 100) + 0.12 * cl01(dd, -5, 0)
                + 0.20 * (cl01(vac, 1.0, 3.0) * 0.6 + cl01(vacd, 0, 0.8) * 0.4)
                + 0.20 * cl01(3 - rentg, 0, 8) + 0.16 * cl01(stockg, 0, 25)
                + 0.10 * (cl01((h4 + 1) / 2, 0, 1) * (1 - cl01((h1 + 1) / 2, 0, 1))))
        m12 = (price / P.v[k - 53] - 1) * 100 if k >= 53 and P.v[k - 53] else None
        rows.append({"code": code, "name": r["name"], "state": r["state"], "buy": buy, "sell": sell,
                     "m12": m12, "yld": yld, "ypc": ypc, "vac": vac, "vacd": vacd, "rentg": rentg,
                     "stockg": stockg, "dd": dd})
    return rows

def fwd(P, asof, months):
    k = P.idx(asof)
    if k < 1: return None
    a = P.v[k - 1]
    end = (datetime.strptime(asof, "%Y-%m-%d") + timedelta(days=int(months * 30.44))).strftime("%Y-%m-%d")
    if not P.d or end > P.d[-1]: return None
    k2 = P.idx(end)
    if k2 < 1: return None
    b = P.v[k2 - 1]
    return (b / a - 1) * 100 if a and b else None

def month_ends(start, stop):
    y, m = int(start[:4]), int(start[5:7]); out = []
    while f"{y:04d}-{m:02d}" <= stop:
        last = (datetime(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
        out.append(datetime(y, m, last)); m += 1
        if m == 13: y, m = y + 1, 1
    return out

def crosscheck(regs, raw_regions, dates):
    worst = 0.0
    for dt in dates:
        asof = dt.strftime("%Y-%m-%d"); asof_m = dt.strftime("%Y-%m")
        a = {r["code"]: (r["buy"], r["sell"]) for r in score_asof_fast(regs, asof, asof_m)}
        b = {r["code"]: (r["buy"], r["sell"]) for r in _orig.score_asof(raw_regions, asof, asof_m)}
        if set(a) != set(b):
            raise SystemExit(f"CROSSCHECK FAILED {asof}: eligible sets differ ({len(a)} vs {len(b)})")
        for c in a:
            worst = max(worst, abs(a[c][0] - b[c][0]), abs(a[c][1] - b[c][1]))
    if worst > 1e-9:
        raise SystemExit(f"CROSSCHECK FAILED: max |diff| = {worst}")
    return worst

def spread(rows, fk, sk="buy", frac=0.1, rev=False):
    rows = [r for r in rows if r.get(fk) is not None and r.get(sk) is not None]
    if len(rows) < 100: return None
    rows.sort(key=lambda r: r[sk], reverse=rev); n = len(rows); k = max(1, int(n * frac))
    return st.mean(r[fk] for r in rows[-k:]) - st.mean(r[fk] for r in rows[:k])

def tstat(v):
    if len(v) < 3: return None
    m = st.mean(v); s = st.stdev(v)
    return {"mean": round(m, 3), "sd": round(s, 3), "t": round(m / (s / math.sqrt(len(v))), 2) if s else None,
            "pct_positive": round(100 * sum(1 for x in v if x > 0) / len(v), 1), "n": len(v)}

def main():
    start = sys.argv[sys.argv.index("--start") + 1] if "--start" in sys.argv else "2014-07"
    regs, raw, baked = load()
    last_px = max((r["px"].d[-1] for r in regs.values() if r["px"].d), default=None)
    stop = (datetime.strptime(last_px, "%Y-%m-%d") - timedelta(days=200)).strftime("%Y-%m") if last_px else "2099-12"
    months = month_ends(start, stop)
    print(f"history baked {baked} · last px {last_px} · scoring {months[0]:%Y-%m} → {months[-1]:%Y-%m} ({len(months)} months)")

    xc = crosscheck(regs, raw, [months[0], months[len(months) // 2], months[-1]])
    print(f"formula cross-check vs property-backtest.score_asof: OK (max |diff| {xc:.1e})")

    bench = regs.get("CAP8", {}).get("px") or regs.get("AUS", {}).get("px")
    D = []
    for dt in months:
        asof = dt.strftime("%Y-%m-%d"); asof_m = dt.strftime("%Y-%m")
        rows = score_asof_fast(regs, asof, asof_m)
        if len(rows) < 50: continue
        for r in rows:
            P = regs[r["code"]]["px"]
            for h in HORIZONS: r[f"f{h}"] = fwd(P, asof, h)
        D.append({"asof": asof, "rows": rows})

    # ── 1. decile curves (pooled, excess over monthly universe median) ──────────
    deciles = {}; spreads = {}; monotone = {}
    for h in HORIZONS:
        key = f"f{h}"; buckets = {d: [] for d in range(10)}
        for m in D:
            rows = [r for r in m["rows"] if r[key] is not None]
            if len(rows) < 100: continue
            mm = st.median(r[key] for r in rows); rows.sort(key=lambda r: r["buy"]); n = len(rows)
            for i, r in enumerate(rows): buckets[min(9, i * 10 // n)].append(r[key] - mm)
        means = [round(st.mean(buckets[d]), 2) if buckets[d] else None for d in range(10)]
        if None in means: continue
        deciles[f"h{h}"] = means
        spreads[f"h{h}"] = round(means[9] - means[0], 2)
        monotone[f"h{h}"] = sum(1 for a, b in zip(means, means[1:]) if b > a)

    # ── 2. monthly top-minus-bottom spread (independent cross-sections) ────────
    monthly = {}
    for h in HORIZONS:
        v = [s for s in (spread(m["rows"], f"f{h}") for m in D) if s is not None]
        if v: monthly[f"h{h}"] = tstat(v)

    # ── 3. state-neutral ───────────────────────────────────────────────────────
    neutral = {}
    for h in HORIZONS:
        raw_v = []; neu_v = []
        for m in D:
            rows = [dict(r) for r in m["rows"] if r[f"f{h}"] is not None]
            if len(rows) < 100: continue
            byst = {}
            for r in rows: byst.setdefault(r["state"], []).append(r)
            for s, rs in byst.items():
                if len(rs) < 5: continue
                mb = st.mean(x["buy"] for x in rs); mf = st.mean(x[f"f{h}"] for x in rs)
                for x in rs: x["buy_n"] = x["buy"] - mb; x["f_n"] = x[f"f{h}"] - mf
            rows = [r for r in rows if "buy_n" in r]
            a = spread(m["rows"], f"f{h}"); b = spread(rows, "f_n", sk="buy_n")
            if a is not None and b is not None: raw_v.append(a); neu_v.append(b)
        if raw_v:
            ra, rn = st.mean(raw_v), st.mean(neu_v)
            neutral[f"h{h}"] = {"raw": round(ra, 2), "state_neutral": round(rn, 2),
                                "survives_pct": round(100 * rn / ra, 0) if ra else None}

    # ── 4. eras ────────────────────────────────────────────────────────────────
    eras = []
    for a, b, lab in ERAS:
        e = {"label": lab, "start": a, "end": b}
        for h in (12, 24):
            v = [s for s in (spread(m["rows"], f"f{h}") for m in D if a <= m["asof"][:7] <= b) if s is not None]
            if v: e[f"h{h}"] = tstat(v)
        eras.append(e)

    # ── 5. factor horse race ───────────────────────────────────────────────────
    FACS = [("buy", "composite buy score", False), ("m12", "trailing 12m price momentum", False),
            ("rentg", "rent growth 12m", False), ("ypc", "yield percentile", False), ("yld", "rental yield", False),
            ("vac", "vacancy (low=good)", True), ("stockg", "listings growth (falling=good)", True),
            ("dd", "drawdown from own high", False)]
    factors = {}
    for h in (12, 24):
        out = []
        for sk, lab, rev in FACS:
            v = [x for x in (spread(m["rows"], f"f{h}", sk, rev=rev) for m in D) if x is not None]
            if v: out.append({"factor": lab, **tstat(v)})
        factors[f"h{h}"] = out

    # ── 6. current placement of pinned markets + top decile (latest scored month) ──
    last = D[-1]; rows = sorted(last["rows"], key=lambda r: r["buy"]); n = len(rows)
    rank = {r["code"]: i for i, r in enumerate(rows)}
    d12 = deciles.get("h12"); d24 = deciles.get("h24")
    def place(code):
        r = next((x for x in rows if x["code"] == code), None)
        if not r: return {"code": code, "eligible": False}
        pc = 100 * (rank[code] + 1) / n; d = min(9, int(pc // 10))
        return {"code": code, "name": r["name"], "state": r["state"], "eligible": True,
                "buy": round(r["buy"], 3), "percentile": round(pc, 0), "decile": d,
                "vac": r["vac"], "vac_delta12": round(r["vacd"], 2), "yield": r["yld"], "yield_pctile": round(r["ypc"], 0),
                "rent12": round(r["rentg"], 1), "listings12": round(r["stockg"], 1), "dd": round(r["dd"], 1),
                "fcast_excess_12m": d12[d] if d12 else None, "fcast_excess_24m": d24[d] if d24 else None}
    pinned = [place(c) for c in PINNED]
    top = [place(r["code"]) for r in rows[-max(1, n // 10):]][::-1]

    result = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "history_baked": baked, "last_px": last_px,
              "window": {"start": D[0]["asof"], "end": D[-1]["asof"], "months": len(D)},
              "placement_asof": last["asof"],
              "crosscheck": {"months_checked": 3, "max_abs_diff": xc, "ok": True},
              "deciles": deciles, "spread_top_minus_bottom": spreads, "monotone_steps_of_9": monotone,
              "monthly_spread": monthly, "state_neutral": neutral, "eras": eras, "factors": factors,
              "pinned": pinned, "top_decile_now": top,
              "notes": ["excess = forward index change minus that month's universe median",
                        "t-stats overstate significance (overlapping horizons); era consistency is the evidence",
                        "index != tradeable; ~8% round-trip means this is a 24m+ signal",
                        "placement/pinned reflect the LAST month in the history file — re-bake before relying on them"]}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(result, f, indent=1)
    os.replace(tmp, OUT)
    print(f"\nwrote {OUT}")
    for h in HORIZONS:
        if f"h{h}" in deciles:
            print(f"  {h:2d}m  D0 {deciles[f'h{h}'][0]:+6.2f}  D9 {deciles[f'h{h}'][9]:+6.2f}  spread {spreads[f'h{h}']:+6.2f}  monotone {monotone[f'h{h}']}/9")
    print("  pinned:", ", ".join(f"{p['code']} D{p['decile']}" if p["eligible"] else f"{p['code']} n/a" for p in pinned))

if __name__ == "__main__":
    main()
