"""
property-forecast.py — 10-year probability fan for every market on the board.
══════════════════════════════════════════════════════════════════════════════
Added 2026-11-14. Writes data/property-forecast.json (small; safe to commit).

A FAN, NOT A LINE. Nobody can point-forecast a housing market ten years out.
What the data CAN support is a distribution, and a measured statement of how
well that distribution has held up out-of-sample.

METHOD (fixed before the first run — do not tune after looking at results)
  base   For each horizon h (6..120 months): the pooled empirical distribution of
         h-month log price changes across EVERY market and EVERY start date in
         the SQM history. "What an h-year stretch in an Australian housing market
         has actually looked like." Deliberately NOT one market's own history
         extrapolated — one market has ~1.7 independent decades of data.
  tilt   The validated buy-score decile excess (12/24/36m, see
         property-decile-validation.py), added for years 0-3 and held flat after.
         SHIPPED ONLY IF it beats the untilted fan on out-of-sample pinball loss
         at BOTH 3y and 5y. Otherwise dropped and the JSON says so.
  width  Conformal calibration: rebuild the fan at past dates using only data
         available then, measure how often reality landed inside the 80% band,
         and scale the band so that it would have been honest. Never narrowed
         below the raw empirical width (k floored at 1.0).

WHAT CANNOT BE TESTED (say this wherever the fan is shown)
  * Years 6-10: with ~17 years of data no 10-year forecast can be scored
    out-of-sample. Those years use the widening measured at 3-5 years.
  * One macro history: 2009-2026 contains the largest fall in interest rates on
    record. A decade unlike any in the sample is not in the fan.
  * Index != house: this is the SQM asking-price index for a postcode. A single
    property carries far more idiosyncratic risk than the band shows.

    python backtests/property-forecast.py
"""
import json, os, sys, math, statistics as st, importlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# --type h|u builds the houses / units fan from the typed SQM series (px_h / px_u) into
# data/property-forecast-h.json / -u.json. Same method, same pre-registered tilt test, run
# separately per type — the tilt only ships for a type if it passes on that type's data.
DTYPE = sys.argv[sys.argv.index("--type") + 1] if "--type" in sys.argv else None
assert DTYPE in (None, "h", "u"), "--type must be h or u"
OUT = os.path.join(ROOT, "data", "property-forecast.json" if not DTYPE else "property-forecast-%s.json" % DTYPE)
sys.path.insert(0, HERE)
V = importlib.import_module("property-decile-validation")

H = list(range(6, 121, 6))                 # horizons in months
Q = [0.10, 0.25, 0.50, 0.75, 0.90]
CAL_H = (36, 60)                           # horizons that CAN be scored out-of-sample
TILT_H = (12, 24, 36)

def quantile(s, q):
    if not s: return None
    x = q * (len(s) - 1); lo = int(math.floor(x)); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (x - lo)

def metrics(recs):
    """recs: list of (realised_log, [q10,q25,q50,q75,q90])"""
    if not recs: return None
    n = len(recs)
    cov80 = sum(1 for r, q in recs if q[0] <= r <= q[4]) / n
    cov50 = sum(1 for r, q in recs if q[1] <= r <= q[3]) / n
    bias = st.mean(r - q[2] for r, q in recs)
    mae = st.mean(abs(r - q[2]) for r, q in recs)
    pin = 0.0
    for r, q in recs:
        for lev, qv in zip(Q, q):
            d = r - qv; pin += (lev * d if d >= 0 else (lev - 1) * d)
    return {"n": n, "coverage_80": round(100 * cov80, 1), "coverage_50": round(100 * cov50, 1),
            "median_bias_log": round(bias, 4), "mae_log": round(mae, 4), "pinball": round(pin / (n * len(Q)), 5)}

def conformal_k(recs):
    z = []
    for r, q in recs:
        up = q[4] - q[2]; dn = q[2] - q[0]
        if r >= q[2]: z.append((r - q[2]) / up if up > 1e-9 else 0.0)
        else:         z.append((q[2] - r) / dn if dn > 1e-9 else 0.0)
    z.sort()
    return quantile(z, 0.80)

def main():
    regs, raw, baked = V.load("px_" + DTYPE if DTYPE else "px")
    last_px = max(r["px"].d[-1] for r in regs.values() if r["px"].d)
    grid = [d.strftime("%Y-%m-%d") for d in V.month_ends("2009-06", last_px[:7])]
    grid = [d for d in grid if d <= last_px]
    N = len(grid); LAST = N - 1
    codes = [c for c, r in regs.items() if r["state"] != "NAT"]
    logp = {}
    for c in codes:
        P = regs[c]["px"]; row = []
        for d in grid:
            k = P.idx(d); v = P.v[k - 1] if k >= 1 else None
            row.append(math.log(v) if v and v > 0 else None)
        logp[c] = row
    print(f"history baked {baked} · last px {last_px} · {len(codes)} markets · {N} months ({grid[0]} → {grid[-1]})")

    def pooled(h, upto):
        out = []
        for c in codes:
            lp = logp[c]
            for j in range(h, upto + 1):
                a = lp[j - h]; b = lp[j]
                if a is not None and b is not None: out.append(b - a)
        out.sort(); return out

    # ── monthly cross-sections: decile of every eligible market + forward excess sums ──
    first = next(i for i, d in enumerate(grid) if d[:7] >= "2014-07")
    dec_of = {}                                 # grid idx -> {code: decile}
    ex = {h: {} for h in TILT_H}                # h -> grid idx -> ([sum]*10, [n]*10)
    for i in range(first, N):
        rows = V.score_asof_fast(regs, grid[i], grid[i][:7])
        if len(rows) < 50: continue
        rows.sort(key=lambda r: r["buy"]); n = len(rows)
        dmap = {r["code"]: min(9, k * 10 // n) for k, r in enumerate(rows)}
        dec_of[i] = dmap
        for h in TILT_H:
            if i + h > LAST: continue
            f = {}
            for c in dmap:
                a = logp[c][i]; b = logp[c][i + h]
                if a is not None and b is not None: f[c] = (math.exp(b - a) - 1) * 100
            if len(f) < 100: continue
            med = st.median(f.values()); s = [0.0] * 10; cnt = [0] * 10
            for c, v in f.items(): s[dmap[c]] += v - med; cnt[dmap[c]] += 1
            ex[h][i] = (s, cnt)
    scored = sorted(dec_of)
    print(f"scored cross-sections: {len(scored)} months ({grid[scored[0]]} → {grid[scored[-1]]})")

    def curve(h, upto):
        """decile excess (pp) from cross-sections whose outcome was known by grid idx `upto`."""
        s = [0.0] * 10; cnt = [0] * 10
        for i, (ss, cc) in ex[h].items():
            if i + h <= upto:
                for d in range(10): s[d] += ss[d]; cnt[d] += cc[d]
        if min(cnt) < 200: return None
        return [s[d] / cnt[d] for d in range(10)]

    # ── out-of-sample calibration ──────────────────────────────────────────────
    recs = {h: {"A": [], "B": [], "A_common": [], "byvol": {0: [], 1: [], 2: []}} for h in CAL_H}
    asofs = [i for i in scored if (i - scored[0]) % 6 == 0]
    for t in asofs:
        vols = {}
        for c in dec_of[t]:
            lp = [x for x in logp[c][:t + 1] if x is not None]
            if len(lp) >= 37: vols[c] = st.pstdev([b - a for a, b in zip(lp, lp[1:])])
        vs = sorted(vols.values())
        cut = (quantile(vs, 1 / 3), quantile(vs, 2 / 3)) if vs else (0, 0)
        for h in CAL_H:
            if t + h > LAST: continue
            pool = pooled(h, t)
            if len(pool) < 5000: continue
            qA = [quantile(pool, q) for q in Q]
            cv = curve(36, t)
            for c, d in dec_of[t].items():
                a = logp[c][t]; b = logp[c][t + h]
                if a is None or b is None: continue
                r = b - a
                recs[h]["A"].append((r, qA))
                if c in vols:
                    recs[h]["byvol"][0 if vols[c] <= cut[0] else 1 if vols[c] <= cut[1] else 2].append((r, qA))
                if cv:
                    qB = [math.log(max(1e-6, math.exp(q) + cv[d] / 100)) for q in qA]
                    recs[h]["B"].append((r, qB)); recs[h]["A_common"].append((r, qA))

    cal = {}; tilt_wins = True
    for h in CAL_H:
        mA = metrics(recs[h]["A"]); mAc = metrics(recs[h]["A_common"]); mB = metrics(recs[h]["B"])
        cal[f"h{h}"] = {"untilted_all": mA, "untilted_same_sample": mAc, "tilted_same_sample": mB,
                        "by_volatility_tercile": [metrics(recs[h]["byvol"][k]) for k in range(3)]}
        if not (mAc and mB and mB["pinball"] < mAc["pinball"]): tilt_wins = False
    model = "B_tilted" if tilt_wins else "A_untilted"
    use = "B" if tilt_wins else "A"
    k = {h: (conformal_k(recs[h][use]) if recs[h][use] else None) for h in CAL_H}
    print(f"\nPRE-REGISTERED RULE: ship the tilt only if it beats untilted pinball at BOTH {CAL_H} months → {model}")
    for h in CAL_H:
        c = cal[f"h{h}"]
        print(f"  {h}m untilted(all)  n={c['untilted_all']['n']:6d} cov80={c['untilted_all']['coverage_80']:5.1f}% cov50={c['untilted_all']['coverage_50']:5.1f}% bias={c['untilted_all']['median_bias_log']:+.3f}")
        if c["tilted_same_sample"]:
            print(f"  {h}m same-sample    pinball untilted={c['untilted_same_sample']['pinball']:.5f}  tilted={c['tilted_same_sample']['pinball']:.5f}"
                  f"   cov80 untilted={c['untilted_same_sample']['coverage_80']}% tilted={c['tilted_same_sample']['coverage_80']}%")
        print(f"  {h}m by vol tercile cov80: " + " / ".join(str(m['coverage_80']) if m else "-" for m in c["by_volatility_tercile"]) + f"   conformal k={k[h]:.3f}")

    # ── persistence of relative growth: does a market's past 5y predict its next 5y? ──
    pers = []
    for s_ in range(60, LAST - 60 + 1, 12):
        xs = []; ys = []
        for c in codes:
            a, b, d = logp[c][s_ - 60], logp[c][s_], logp[c][s_ + 60]
            if None not in (a, b, d): xs.append(b - a); ys.append(d - b)
        if len(xs) > 100:
            mx, my = st.mean(xs), st.mean(ys)
            cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            rho = cov / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
            pers.append({"split": grid[s_], "n": len(xs), "rho": round(rho, 3)})
    print("\npersistence (past 5y vs next 5y, cross-market ρ): " + ", ".join(f"{p['split'][:7]} {p['rho']:+.2f}" for p in pers))

    # ── production fan ─────────────────────────────────────────────────────────
    k36 = max(1.0, k[36] or 1.0); k60 = max(1.0, k[60] or 1.0)
    def kh(h): return k36 if h <= 36 else k60 if h >= 60 else k36 + (k60 - k36) * (h - 36) / 24
    base, base_raw, pool_n = [], [], []
    for h in H:
        pool = pooled(h, LAST); pool_n.append(len(pool))
        q = [quantile(pool, x) for x in Q]; med = q[2]; kk = kh(h)
        base_raw.append([round(math.exp(x), 4) for x in q])
        base.append([round(math.exp(med + kk * (x - med)), 4) for x in q])
    full = {h: curve(h, LAST) for h in TILT_H}
    tilt = {}
    for d in range(10):
        pts = [(0, 0.0)] + [(h, full[h][d]) for h in TILT_H if full[h]]
        row = []
        for h in H:
            if not tilt_wins: row.append(0.0); continue
            if h >= pts[-1][0]: row.append(round(pts[-1][1], 2)); continue
            for (h0, e0), (h1, e1) in zip(pts, pts[1:]):
                if h0 <= h <= h1: row.append(round(e0 + (e1 - e0) * (h - h0) / (h1 - h0), 2)); break
        tilt[str(d)] = row
    last_scored = scored[-1]
    markets = {c: {"d": d} for c, d in sorted(dec_of[last_scored].items())}

    out = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "dtype": DTYPE or "all",
           "history_baked": baked, "asof": grid[LAST], "deciles_asof": grid[last_scored],
           "model": model, "horizons_m": H, "quantiles": Q,
           "base": base, "base_raw": base_raw, "pool_n": pool_n,
           "conformal": {"k36": round(k[36], 3) if k[36] else None, "k60": round(k[60], 3) if k[60] else None,
                         "applied": [round(kh(h), 3) for h in H], "floor": 1.0},
           "tilt_pp": tilt, "markets": markets,
           "calibration": cal, "persistence_5y": pers,
           "untestable_beyond_m": max(CAL_H),
           "notes": ["ratio = price multiple of today's index level; nominal, not inflation-adjusted",
                     "base = pooled empirical distribution across all markets and start dates, conformally widened",
                     "tilt = validated decile excess (pp), years 0-3 then held; zero if it failed the pre-registered test",
                     f"horizons beyond {max(CAL_H)} months cannot be scored out-of-sample with this history",
                     "single macro history 2009-2026 (includes a record fall in interest rates)",
                     "index of asking prices for a postcode — not a valuation of any single property"]}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(out, f, separators=(",", ":"))
    os.replace(tmp, OUT)
    print(f"\nwrote {OUT} ({os.path.getsize(OUT)//1024} KB) · model {model} · k36 {k36:.2f} k60 {k60:.2f}")
    for h, b, br in zip(H, base, base_raw):
        if h in (12, 36, 60, 120):
            cg = lambda r: (r ** (12 / h) - 1) * 100
            print(f"  {h:3d}m  p10 {b[0]:.3f} ({cg(b[0]):+.1f}%/yr)  p50 {b[2]:.3f} ({cg(b[2]):+.1f}%/yr)  p90 {b[4]:.3f} ({cg(b[4]):+.1f}%/yr)   raw p10/p90 {br[0]:.3f}/{br[4]:.3f}")

if __name__ == "__main__":
    main()
