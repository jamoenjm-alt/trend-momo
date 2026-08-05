"""
property-lab.py — a bench for testing property-picking theories
════════════════════════════════════════════════════════════════

The board ships ONE model. This lets you ask whether that model is actually
any good, and which parts of it are doing the work.

Define a theory as a set of factor weights, and the lab walks forward month by
month using only data that existed at the time, picks markets, then measures
what those markets actually did over the next 6 / 12 / 24 months — against the
median market, which is the only benchmark that says whether the pick added
anything.

    python backtests/property-lab.py                 # all theories, 3 years
    python backtests/property-lab.py --years 5
    python backtests/property-lab.py --only current,pure_value

Reads data/property-history.json (written by update-property.py, gitignored).

FACTORS — each returns 0..1, higher = more attractive to BUY
  value    yield percentile vs the market's OWN history   (cheap vs itself)
  income   absolute gross yield, capped at 5.5%           (cashflow, no trap)
  dip      how far below its 10y peak                     (entry discount)
  vac      rental tightness (low vacancy)                 (demand)
  rent     12m rent growth                                (rents lead prices)
  supply   listings falling                               (tightening market)
  trend    long-term up, short-term dipped                (buy the pullback)

CONTROLS — always run, and the reason to trust or distrust everything else
  random   picks at random from the eligible set
  inverse  the current model, upside down

Add a theory by adding one line to STRATEGIES. That is the whole point.
"""

import bisect
import json
import os
import statistics as st
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HIST = os.path.join(ROOT, "data", "property-history.json")
OUT = os.path.join(HERE, "property-lab-results.json")

MIN_LISTINGS = 100
MIN_WEEKS = 260
MA_PAIRS = [(12, 4, "h1"), (18, 6, "h1"), (26, 9, "h1"),
            (33, 11, "h2"), (39, 13, "h2"), (52, 17, "h2"),
            (65, 22, "h3"), (78, 26, "h3"), (104, 35, "h3"),
            (130, 43, "h4"), (195, 65, "h4"), (260, 87, "h4")]

# ── THEORIES ────────────────────────────────────────────────────────────────
# weights need not sum to 1; they are normalised. use_risk applies the
# capital-risk discount (deep historical busts + thin listings).
STRATEGIES = {
    "current":     dict(w=dict(value=.20, income=.10, dip=.12, vac=.20,
                               rent=.20, supply=.10, trend=.08), use_risk=True),
    "pure_value":  dict(w=dict(value=1.0), use_risk=False),
    "pure_income": dict(w=dict(income=1.0), use_risk=False),
    "pure_trend":  dict(w=dict(trend=1.0), use_risk=False),
    "rental_only": dict(w=dict(vac=.5, rent=.5), use_risk=False),
    "supply_only": dict(w=dict(supply=1.0), use_risk=False),
    "contrarian":  dict(w=dict(dip=1.0), use_risk=False),
    "value_rent":  dict(w=dict(value=.5, rent=.5), use_risk=False),
    "no_trend":    dict(w=dict(value=.22, income=.11, dip=.13, vac=.22,
                               rent=.22, supply=.10), use_risk=True),
    "equal":       dict(w=dict(value=1, income=1, dip=1, vac=1,
                               rent=1, supply=1, trend=1), use_risk=False),
}


def cl(x, lo, hi):
    if x is None:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def sma(seq, w):
    return sum(seq[-w:]) / w if len(seq) >= w else None


def trend_cols(px):
    if len(px) < 30:
        return None, None
    price = px[-1]
    mas = {n: sma(px, n) for n in {p for pr in MA_PAIRS for p in pr[:2]} if len(px) >= n}
    grp = {"h1": [], "h4": []}
    for slow, fast, g in MA_PAIRS:
        if g not in grp:
            continue
        s, f = mas.get(slow), mas.get(fast)
        if s is not None:
            grp[g].append(1 if price > s else -1)
        if s is not None and f is not None:
            grp[g].append(1 if f > s else -1)
    h1 = sum(grp["h1"]) / len(grp["h1"]) if grp["h1"] else 0.0
    h4 = sum(grp["h4"]) / len(grp["h4"]) if grp["h4"] else 0.0
    return h1, h4


class Series:
    """date-indexed series with as-of lookup."""
    __slots__ = ("d", "v")

    def __init__(self, pairs):
        pairs = sorted(pairs or [])
        self.d = [p[0] for p in pairs]
        self.v = [p[1] for p in pairs]

    def upto(self, asof):
        i = bisect.bisect_right(self.d, asof)
        return self.v[:i]

    def at(self, asof):
        i = bisect.bisect_right(self.d, asof) - 1
        return self.v[i] if i >= 0 else None

    def last_date(self):
        return self.d[-1] if self.d else None


def load():
    with open(HIST, encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for code, r in raw["regions"].items():
        if r.get("state") == "NAT" or not r.get("px"):
            continue
        out[code] = {
            "name": r["name"], "state": r["state"],
            "px": Series(r.get("px")), "rent": Series(r.get("rent")),
            "yield": Series(r.get("yield")), "vac": Series(r.get("vac")),
            "stock": Series(r.get("stock")),
        }
    print(f"loaded {len(out)} markets from {raw.get('updated')}")
    return out


def factors_asof(R, asof, asof_m):
    """Point-in-time factor values for every eligible market."""
    rows = []
    for code, r in R.items():
        px = r["px"].upto(asof)
        if len(px) < MIN_WEEKS:
            continue
        stock = r["stock"].upto(asof_m)
        if len(stock) < 13 or stock[-1] < MIN_LISTINGS:
            continue
        yl = r["yield"].upto(asof)
        vac = r["vac"].upto(asof_m)
        rent = r["rent"].upto(asof)
        if not yl or not vac or len(rent) < 53:
            continue

        y = yl[-1]
        ypc = 100.0 * sum(1 for x in yl if x <= y) / len(yl)
        peak = max(px)
        dd = (px[-1] / peak - 1) * 100
        run, worst = px[0], 0.0
        for v in px:
            run = max(run, v)
            worst = min(worst, v / run - 1)
        ddmax = worst * 100
        rentg = (rent[-1] / rent[-53] - 1) * 100 if rent[-53] else 0.0
        stockg = (stock[-1] / stock[-13] - 1) * 100 if stock[-13] else 0.0
        h1, h4 = trend_cols(px)

        rows.append({
            "code": code, "name": r["name"], "state": r["state"],
            "risk": 1 - (cl(-ddmax, 15, 45) * 0.30 + cl(300 - stock[-1], 0, 200) * 0.10),
            "f": {
                "value":  ypc / 100,
                "income": cl(y, 2.5, 5.5),
                "dip":    cl(-dd, 0, 15),
                "vac":    cl(2.5 - vac[-1], 0, 2.0),
                "rent":   cl(rentg, 0, 10),
                "supply": cl(-stockg, 0, 20),
                "trend":  cl((h4 + 1) / 2, 0, 1) * (1 - cl((h1 + 1) / 2, 0, 1) * 0.5),
            },
        })
    return rows


def score(rows, spec):
    w = spec["w"]
    tot = sum(w.values()) or 1
    for r in rows:
        s = sum(r["f"][k] * v for k, v in w.items()) / tot
        r["s"] = s * (r["risk"] if spec.get("use_risk") else 1.0)
    return rows


def fwd(series, asof, months):
    a = series.at(asof)
    end = (datetime.strptime(asof, "%Y-%m-%d") + timedelta(days=int(months * 30.44))).strftime("%Y-%m-%d")
    if not a or not series.last_date() or end > series.last_date():
        return None
    b = series.at(end)
    return (b / a - 1) * 100 if b else None


def main():
    years = 3
    if "--years" in sys.argv:
        years = int(sys.argv[sys.argv.index("--years") + 1])
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))

    R = load()
    today = datetime.now(timezone.utc)
    months = []
    y, m = today.year, today.month
    for _ in range(years * 12):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        last = (datetime(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
        months.append(datetime(y, m, last))
    months.reverse()

    names = [k for k in STRATEGIES if not only or k in only]
    # acc[strategy][horizon] = list of (pick_excess, top5_excess, state_basket_excess)
    acc = {n: {6: [], 12: [], 24: []} for n in names}
    ctl = {"random": {6: [], 12: [], 24: []}, "inverse": {6: [], 12: [], 24: []}}
    import random
    random.seed(11)
    log = []

    for dt_ in months:
        asof, asof_m = dt_.strftime("%Y-%m-%d"), dt_.strftime("%Y-%m")
        base = factors_asof(R, asof, asof_m)
        if len(base) < 30:
            continue
        fw = {hz: {r["code"]: fwd(R[r["code"]]["px"], asof, hz) for r in base} for hz in (6, 12, 24)}
        med = {hz: (st.median([v for v in fw[hz].values() if v is not None])
                    if any(v is not None for v in fw[hz].values()) else None)
               for hz in (6, 12, 24)}

        entry = {"asof": asof, "eligible": len(base)}
        for n in names:
            rows = score([dict(r) for r in base], STRATEGIES[n])
            rows.sort(key=lambda r: -r["s"])
            entry[n] = rows[0]["name"] + " (" + rows[0]["state"] + ")"
            # per-state best, equal-weighted basket
            seen, basket = set(), []
            for r in rows:
                if r["state"] not in seen:
                    seen.add(r["state"]); basket.append(r["code"])
            for hz in (6, 12, 24):
                if med[hz] is None:
                    continue
                p1 = fw[hz].get(rows[0]["code"])
                t5 = [fw[hz].get(r["code"]) for r in rows[:5]]
                t5 = [x for x in t5 if x is not None]
                sb = [fw[hz].get(c) for c in basket]
                sb = [x for x in sb if x is not None]
                if p1 is None or not t5 or not sb:
                    continue
                acc[n][hz].append((p1 - med[hz],
                                   sum(t5) / len(t5) - med[hz],
                                   sum(sb) / len(sb) - med[hz]))
        # controls
        rows = score([dict(r) for r in base], STRATEGIES["current"])
        rows.sort(key=lambda r: -r["s"])
        for hz in (6, 12, 24):
            if med[hz] is None:
                continue
            rnd = [fw[hz].get(r["code"]) for r in random.sample(rows, min(5, len(rows)))]
            rnd = [x for x in rnd if x is not None]
            inv = [fw[hz].get(r["code"]) for r in rows[-5:]]
            inv = [x for x in inv if x is not None]
            if rnd:
                ctl["random"][hz].append((sum(rnd) / len(rnd) - med[hz],) * 3)
            if inv:
                ctl["inverse"][hz].append((sum(inv) / len(inv) - med[hz],) * 3)
        log.append(entry)

    avg = lambda xs: sum(xs) / len(xs) if xs else None
    print("\n" + "=" * 96)
    print("EXCESS RETURN vs the MEDIAN eligible market, by theory")
    print("  top1 = single best pick   top5 = best five, equal weight   state = best in each state")
    print("=" * 96)
    hdr = f"{'theory':14}{'n':>4}" + "".join(f"{h:>26}" for h in ("6 months", "12 months", "24 months"))
    print(hdr)
    print(f"{'':18}" + "".join(f"{'top1':>8}{'top5':>9}{'state':>9}" for _ in range(3)))
    for n in names + ["random", "inverse"]:
        src = acc.get(n) or ctl[n]
        cells, nn = "", 0
        for hz in (6, 12, 24):
            v = src[hz]
            nn = max(nn, len(v))
            if not v:
                cells += f"{'—':>8}{'—':>9}{'—':>9}"
            else:
                cells += (f"{avg([x[0] for x in v]):>+8.1f}"
                          f"{avg([x[1] for x in v]):>+9.1f}"
                          f"{avg([x[2] for x in v]):>+9.1f}")
        mark = "  <- control" if n in ctl else ""
        print(f"{n:14}{nn:>4}{cells}{mark}")

    print("\nbeat rate (share of months the top-1 pick beat the median):")
    for n in names:
        v = acc[n][12]
        if v:
            print(f"  {n:14} 12m {100*sum(1 for x in v if x[0] > 0)/len(v):5.0f}%   n={len(v)}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"generated": today.strftime("%Y-%m-%dT%H:%M:%SZ"), "years": years,
                   "strategies": {k: STRATEGIES[k] for k in names},
                   "monthly_picks": log,
                   "summary": {n: {str(hz): {"n": len(acc[n][hz]),
                                             "top1": avg([x[0] for x in acc[n][hz]]),
                                             "top5": avg([x[1] for x in acc[n][hz]]),
                                             "state": avg([x[2] for x in acc[n][hz]])}
                                   for hz in (6, 12, 24)} for n in names}}, f, indent=1)
    print(f"\nwrote {OUT}")
    print("\nRead the controls first. If 'random' is near zero and 'inverse' is negative,")
    print("the ranking carries information. If not, nothing above it means anything.")


if __name__ == "__main__":
    main()
