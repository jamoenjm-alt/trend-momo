"""Regime-conditioned base-rate backtest (16 Nov 2026). No look-ahead.
Data: Dallas Fed IHPD hp2602 (real prices, real disposable income), BIS CBPOL policy rates (quarterly, end of period).
Target: next-5y real house price change, per country-year (Q4 to Q4).
At each origin year T, training set = country-years t with t+5 <= T (outcome known at T). Predict for every country at T.
Models: B1 zero real change | U unconditional median | V valuation-decile | VI valuation+income-fell | VR valuation+rates-rising | VIR all three.
Conditioned models fall back to the next-coarser model when the matching training set has < MIN_N obs.
Scored by pinball loss (q=.1,.5,.9) and MAE of median, plus 80% interval coverage."""
import pandas as pd, numpy as np, json
d = pd.read_csv('../raw/dallasfed_ihpd_annual_q4.csv'); d['yr'] = d.period.str[:4].astype(int); d = d.set_index('yr')
cb = pd.read_csv('../raw/bis_cbpol_quarterly.csv'); cb['yr'] = cb.period.str[:4].astype(int)
MAP = {'AUS':'AU','NZL':'NZ','CAN':'CA','GBR':'GB','IRL':'IE','NLD':'NL','SWE':'SE','NOR':'NO','DNK':'DK','USA':'US','ESP':'ES','JPN':'JP'}
EA = {'IRL','NLD','ESP'}
def rate(c):
    s = cb.groupby('yr')[MAP[c]].mean()
    if c in EA: s = s.combine_first(cb.groupby('yr')['XM'].mean()) if c=='IRL' else s.where(s.index<1999, cb.groupby('yr')['XM'].mean())
    return s
rows = []
for c in MAP:
    p, y = d['rhpi_'+c], d['rpdi_'+c]; pi = p/y; r = rate(c)
    for t in d.index:
        if t < 1980 or pd.isna(pi[t]): continue
        hist = pi.loc[:t].dropna()
        if len(hist) < 10: continue
        r10 = r.loc[t-10:t-1].mean() if t-10 >= r.index.min() else np.nan
        rows.append(dict(c=c, t=t, pct=(hist<=pi[t]).mean(), inc1=y[t]/y.get(t-1,np.nan)-1,
            dr1=r.get(t,np.nan)-r.get(t-1,np.nan), rgap=r.get(t,np.nan)-r10,
            f5=np.log(p.get(t+5,np.nan)/p[t])))
R = pd.DataFrame(rows)
R['V'] = R.pct >= .9
R['I'] = R.inc1 < 0
R['Rr'] = (R.dr1 >= .5) | (R.rgap >= 1.0)   # rates rising OR well above own 10y average
MIN_N = 8; QS = [.1,.5,.9]
def q(x): return np.quantile(x, QS)
def predict(train, row, model):
    if model == 'B1': return np.array([np.nan, 0.0, np.nan])
    sets = {'U': [train],
            'V': [train[train.V==row.V], train],
            'VI': [train[(train.V==row.V)&(train.I==row.I)], train[train.V==row.V], train],
            'VR': [train[(train.V==row.V)&(train.Rr==row.Rr)], train[train.V==row.V], train],
            'VIR':[train[(train.V==row.V)&(train.I==row.I)&(train.Rr==row.Rr)], train[(train.V==row.V)&(train.I==row.I)], train[train.V==row.V], train]}[model]
    for s in sets:
        s = s.dropna(subset=['f5'])
        if len(s) >= MIN_N: return q(s.f5.values)
    return q(train.f5.dropna().values)
def pin(y, qhat, a): return np.maximum(a*(y-qhat), (a-1)*(y-qhat))
res = {m: [] for m in ['B1','U','V','VI','VR','VIR']}
for T in range(1995, 2022):
    train = R[(R.t+5 <= T)].dropna(subset=['f5','Rr'])
    test = R[(R.t==T)].dropna(subset=['f5','inc1'])
    test = test[test.rgap.notna() | test.dr1.notna()]
    for _, row in test.iterrows():
        for m in res:
            qh = predict(train, row, m)
            res[m].append(dict(T=T, c=row.c, y=row.f5, q10=qh[0], q50=qh[1], q90=qh[2]))
out = {}
for m, L in res.items():
    D = pd.DataFrame(L)
    o = dict(n=len(D), mae_med=round(float(np.abs(D.y-D.q50).mean()),4))
    if m != 'B1':
        o['pinball_avg'] = round(float(np.mean([pin(D.y, D['q%d'%int(a*100)], a).mean() for a in QS])),4)
        o['cov80'] = round(float(((D.y>=D.q10)&(D.y<=D.q90)).mean()*100),1)
    for lab, sub in [('pre2008', D[D['T']<2008]), ('2008on', D[D['T']>=2008])]:
        o['mae_'+lab] = round(float(np.abs(sub.y-sub.q50).mean()),4)
    out[m] = o; print(m, o)
# today's reading for Australia
cur = dict(c='AUS')
r = rate('AUS'); p,y = d['rhpi_AUS'], d['rpdi_AUS']; pi=p/y
cur.update(pct=float((pi<=pi[2026]).mean()), inc1=float(y[2026]/y[2025]-1), dr1=float(r[2026]-r[2025]), rgap=float(r[2026]-r.loc[2016:2025].mean()))
print('AUS now', cur)
full = R.dropna(subset=['f5'])
sub = full[(full.V)&(full.Rr)&(full.I)]; sub2 = full[(full.V)&(full.Rr)]
for lab, s in [('V+R+I', sub), ('V+R', sub2)]:
    x = (np.exp(s.f5)-1)*100
    print(lab, 'n',len(s),'countries',s.c.nunique(),'med',round(x.median(),1),'p10',round(x.quantile(.1),1),'p90',round(x.quantile(.9),1),'Pfall',round((x<0).mean()*100))
print(sub[['c','t','pct','inc1','dr1','rgap']].assign(f5=(np.exp(sub.f5)-1).round(3)).round(3).to_string())
json.dump(dict(backtest=out, aus_now=cur), open('../regime_backtest_results.json','w'), indent=1)
