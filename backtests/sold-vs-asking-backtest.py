"""Does combining SQM asking prices with Valuer-General SOLD prices predict better? (16 Nov 2026)
Data: SQM weekly asking index by type (data/property-history.json, local, px_h / px_u)
      VG Victoria annual suburb medians 2015-2025 (data/sold/vic_vg_annual_2015_2025.txt, CC BY 4.0)
Target: next calendar year's VG median sold price (log), per market x type.
Origins Y = 2018..2024 (predict Y+1). Every model is fitted only on years whose outcome was known at Y.
Reported: MAE in log points (x100 ~ % error)."""
import json, numpy as np, pandas as pd, sys
YRS = list(range(2015, 2026))
vg = {}
for line in open('data/sold/vic_vg_annual_2015_2025.txt', encoding='utf-8'):
    if line.startswith('#') or not line.strip(): continue
    code, loc, hs, us = line.rstrip('\n').split('|')
    for t, s in (('h', hs), ('u', us)):
        if not s: continue
        vals = s.split(',')
        for y, v in zip(YRS, vals):
            if v and not v.endswith(('^', '*')):
                vg[(code, t, y)] = float(v) * 100
H = json.load(open('data/property-history.json'))['regions']
def ask_series(code, t):
    r = H.get(code, {}); s = r.get('px_' + t) or []
    df = pd.DataFrame(s, columns=['d', 'v']); df = df[df.v > 0]
    if df.empty: return None
    df['d'] = pd.to_datetime(df.d); return df.set_index('d').v
rows = []
codes = sorted({k[0] for k in vg})
for code in codes:
    for t in 'hu':
        a = ask_series(code, t)
        if a is None: continue
        for y in YRS:
            yr = a[str(y)] if str(y) in a.index.year.astype(str) else None
            ya = a[a.index.year == y]
            if len(ya) < 40: continue
            q4 = ya[ya.index.month >= 10]
            rows.append(dict(code=code, t=t, y=y, sold=vg.get((code, t, y)), ask=ya.mean(), askq4=q4.mean() if len(q4) else np.nan))
D = pd.DataFrame(rows).sort_values(['code', 't', 'y'])
D['ls'] = np.log(D.sold); D['la'] = np.log(D.ask); D['lq'] = np.log(D.askq4)
g = D.groupby(['code', 't'])
D['ls_prev'] = g.ls.shift(1); D['la_prev'] = g.la.shift(1); D['ls_next'] = g.ls.shift(-1)
D['gap'] = D.ls - D.la                                   # log(sold/ask) this year
D['sm'] = D.ls - D.ls_prev                               # sold momentum
D['am'] = D.la - D.la_prev                               # asking momentum (annual avg)
D['aq'] = D.lq - D.la                                    # Q4 asking vs year average (late-year direction)
D['tgt'] = D.ls_next - D.ls                              # next-year sold change
# suburb's own typical sold/ask gap, using only years <= y
D['gap_mean'] = g.gap.transform(lambda s: s.expanding().mean())
D['gap_dev'] = D.gap - D.gap_mean
print('markets x types with data:', D.groupby(['code','t']).ngroups, '| rows with target:', D.tgt.notna().sum())

def ols(tr, cols):
    X = np.c_[np.ones(len(tr)), tr[cols].values]; return np.linalg.lstsq(X, tr.tgt.values, rcond=None)[0]
def pred(b, te, cols): return b[0] + te[cols].values @ b[1:]
MODELS = {
  'B0 no change':                [],
  'B1 avg past change':          None,
  'S  sold momentum':            ['sm'],
  'A  asking momentum':          ['am', 'aq'],
  'G  asking + sold/ask gap':    ['am', 'aq', 'gap_dev'],
  'X  everything':               ['sm', 'am', 'aq', 'gap_dev'],
}
res = {m: [] for m in MODELS}; lev = {k: [] for k in ['L1 last sold', 'L2 asking x own ratio', 'L3 50/50 calibrated', 'L4 raw midpoint']}
for Y in range(2018, 2025):
    tr = D[(D.y <= Y - 1) & D.tgt.notna()].dropna(subset=['sm', 'am', 'aq', 'gap_dev'])
    te = D[(D.y == Y) & D.tgt.notna()].dropna(subset=['sm', 'am', 'aq', 'gap_dev'])
    if len(te) == 0: continue
    for m, cols in MODELS.items():
        if cols == []: p = np.zeros(len(te))
        elif cols is None: p = np.full(len(te), tr.tgt.mean())
        else: p = pred(ols(tr, cols), te, cols)
        res[m] += list(zip(te.t, te.y, np.abs(te.tgt.values - p)))
    # level forecasts of next year's sold price (the "median of the two" question)
    drift = tr.tgt.mean()
    L1 = te.ls + drift
    L2 = te.lq + te.gap_mean + drift * 0.5          # Q4 asking, converted with the market's own sold/ask ratio
    L3 = 0.5 * L1 + 0.5 * L2
    L4 = np.log(0.5 * te.sold + 0.5 * te.askq4) + drift
    for k, L in zip(lev, (L1, L2, L3, L4)):
        lev[k] += list(zip(te.t, te.y, np.abs(te.ls_next - L)))
def summ(d):
    out = {}
    for m, L in d.items():
        a = pd.DataFrame(L, columns=['t', 'y', 'e'])
        out[m] = dict(n=len(a), all=round(a.e.mean() * 100, 2), houses=round(a[a.t == 'h'].e.mean() * 100, 2), units=round(a[a.t == 'u'].e.mean() * 100, 2),
                      worst_year=round(a.groupby('y').e.mean().max() * 100, 2))
        print(f"{m:32s} n={len(a):4d}  MAE all {out[m]['all']:5.2f}%  houses {out[m]['houses']:5.2f}%  units {out[m]['units']:5.2f}%  worst-year {out[m]['worst_year']:5.2f}%")
    return out
print('\n-- next-year SOLD price change (direction/size) --'); r1 = summ(res)
print('\n-- next-year SOLD price level ("median of the two" test) --'); r2 = summ(lev)
# final-fit coefficients for interpretation
tr = D[D.tgt.notna()].dropna(subset=['sm', 'am', 'aq', 'gap_dev'])
b = ols(tr, ['sm', 'am', 'aq', 'gap_dev']); print('\ncoefs (const, sold mom, ask mom, ask Q4 vs yr, gap dev):', np.round(b, 3))
json.dump(dict(change=r1, level=r2, coefs=list(map(float, b))), open('backtests/sold-vs-asking-results.json', 'w'), indent=1)
