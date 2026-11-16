"""1-year-ahead real house price change: does last year's change (momentum) and the rate change predict it? No look-ahead:
rolling OLS fitted on country-years with outcome known at origin T. Dallas Fed IHPD hp2602 + BIS CBPOL. 16 Nov 2026."""
import pandas as pd, numpy as np, json
d = pd.read_csv('../raw/dallasfed_ihpd_annual_q4.csv'); d['yr']=d.period.str[:4].astype(int); d=d.set_index('yr')
cb = pd.read_csv('../raw/bis_cbpol_quarterly.csv'); cb['yr']=cb.period.str[:4].astype(int); cbq4 = cb[cb.period.str.endswith('Q4')].set_index('yr')
MAP={'AUS':'AU','NZL':'NZ','CAN':'CA','GBR':'GB','NLD':'NL','SWE':'SE','NOR':'NO','DNK':'DK','USA':'US','ESP':'ES','JPN':'JP'}
rows=[]
for c,k in MAP.items():
    p=np.log(d['rhpi_'+c]); r=cbq4[k].copy()
    if c in ('NLD','ESP'): r=r.where(r.index<1999, cbq4['XM'])
    for t in d.index:
        if t<1981: continue
        rows.append(dict(c=c,t=t,m1=p.get(t)-p.get(t-1,np.nan),dr=r.get(t,np.nan)-r.get(t-1,np.nan),y=p.get(t+1,np.nan)-p.get(t)))
R=pd.DataFrame(rows).dropna()
def fit(tr,cols):
    X=np.c_[np.ones(len(tr)),tr[cols].values]; return np.linalg.lstsq(X,tr.y.values,rcond=None)[0]
res={'zero':[],'mean':[],'mom':[],'mom_rate':[]}; coefs=[]
for T in range(1995,2026):
    tr=R[R.t+1<=T]; te=R[R.t==T]
    if len(te)==0: continue
    bm=fit(tr,['m1']); br=fit(tr,['m1','dr']); coefs.append((T,*br.round(3)))
    res['zero']+=list(np.abs(te.y)); res['mean']+=list(np.abs(te.y-tr.y.mean()))
    res['mom']+=list(np.abs(te.y-(bm[0]+bm[1]*te.m1))); res['mom_rate']+=list(np.abs(te.y-(br[0]+br[1]*te.m1+br[2]*te.dr)))
out={k:round(float(np.mean(v)),4) for k,v in res.items()}; out['n']=len(res['zero'])
print(out); print('last coefs (T, const, momentum, rate change):', coefs[-1])
json.dump(dict(mae_1y_log=out,last_coefs=list(map(float,coefs[-1][1:]))),open('../momentum_backtest_results.json','w'),indent=1)
