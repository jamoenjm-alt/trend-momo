"""
property-value-buckets.py — does a CHEAPER market (vs its own history) do better? (added 2026-11-16)
═══════════════════════════════════════════════════════════════════════════════════════════════
"Cheap vs its own history" = rental yield percentile vs the market's own yield history to date (no look-ahead;
SQM yield, houses preferred). Buckets: <=20th (houses stretched/expensive), 20-50, 50-80, >80th (cheap).
For each June from 2012, each market's next 36m / 60m log growth (houses px_h, units px_u) minus that year's
cross-market median. Out-of-sample check: bucket means fitted only on start years whose outcome was known.

Findings at build time (history to Jul 2026): expensive-vs-own-history HOUSES lagged (-4.6pp/3y, -7.7pp/5y) and
cheap ones led (+7.1 / +6.5); out-of-sample this improved the houses estimate ~3%. For UNITS the bucket added
nothing out-of-sample. A cheaper market within its STATE (price level) flipped sign by era (cheap lost 2012-15
starts, won 2017-23) — not reliable, not used.
The fan's decile tilt already includes yield-vs-own-history as its biggest input, so this is DISPLAYED as context
on the fan, not added on top (that would double count).

Writes data/property-value-buckets.json.   python backtests/property-value-buckets.py
"""
import json, os
from datetime import datetime, timezone
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "property-history.json")
OUT = os.path.join(ROOT, "data", "property-value-buckets.json")
EDGES = [0, .2, .5, .8, 1.0]
LABELS = ["expensive vs own history (yield ≤20th pct)", "20th–50th", "50th–80th", "cheap vs own history (yield >80th pct)"]


def monthly(pairs):
    s = pd.Series({pd.Timestamp(d): v for d, v in (pairs or []) if v})
    return s.sort_index().resample("ME").last().ffill() if len(s) else None


def main():
    data = json.load(open(HIST, encoding="utf-8"))
    regs = {c: r for c, r in data["regions"].items() if r.get("state") != "NAT"}
    idx = pd.date_range("2011-12-31", max(r["px"][-1][0] for r in regs.values() if r.get("px")), freq="ME")
    S = {t: {} for t in "hu"}; Y = {}
    for c, r in regs.items():
        for t in "hu":
            s = monthly(r.get("px_" + t))
            if s is not None: S[t][c] = s.reindex(idx)
        y = monthly(r.get("yield"))
        if y is not None and len(y) >= 24: Y[c] = y
    def ypct(c, when):
        y = Y.get(c)
        if y is None: return None
        y = y[:when]
        return float((y <= y.iloc[-1]).mean()) if len(y) >= 24 else None
    out = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "history_baked": data.get("updated"),
           "edges": EDGES, "labels": LABELS, "horizons": {}}
    for hz in (36, 60):
        rows = []
        for i, when in enumerate(idx):
            j = i + hz
            if j >= len(idx) or when.month != 6: continue
            for t in "hu":
                g = {}
                for c, s in S[t].items():
                    a, b = s.iloc[i], s.iloc[j]
                    if a == a and b == b and a > 0 and b > 0: g[c] = np.log(b / a)
                if len(g) < 50: continue
                med = float(np.median(list(g.values())))
                for c, v in g.items():
                    yp = ypct(c, when)
                    if yp is not None: rows.append((when.year, t, yp, v - med))
        R = pd.DataFrame(rows, columns=["yr", "t", "yp", "ex"])
        R["b"] = pd.cut(R.yp, EDGES, labels=False, include_lowest=True)
        res = {}
        for t in "hu":
            Rt = R[R.t == t]
            means = Rt.groupby("b").ex.mean()
            errs_t, errs_0 = [], []
            for T in sorted(Rt.yr.unique()):
                tr, te = Rt[Rt.yr <= T - hz // 12], Rt[Rt.yr == T]
                if tr.yr.nunique() < 2: continue
                p = te.b.map(tr.groupby("b").ex.mean()).fillna(0).values
                errs_t += list(np.abs(te.ex.values - p)); errs_0 += list(np.abs(te.ex.values))
            gain = (1 - np.mean(errs_t) / np.mean(errs_0)) * 100 if errs_0 else None
            res[t] = {"excess_pp": [round(float(means.get(k, np.nan)) * 100, 1) for k in range(4)],
                      "n": [int((Rt.b == k).sum()) for k in range(4)],
                      "oos_gain_pct": round(gain, 1) if gain is not None else None,
                      "start_years": [int(Rt.yr.min()), int(Rt.yr.max())]}
            print(f"{hz}m {t}: excess by bucket {res[t]['excess_pp']}  n {res[t]['n']}  OOS gain {res[t]['oos_gain_pct']}%")
        out["horizons"][str(hz)] = res
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(out, f, separators=(",", ":"))
    os.replace(tmp, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
