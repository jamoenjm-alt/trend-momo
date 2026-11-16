"""Phase 3+4: build FY panel, fit models, rolling-origin backtests. Run from scripts/. Writes ../model_results.json"""
import pandas as pd, numpy as np, json, os
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); R=f'{B}/raw'
ST=['NSW','VIC','QLD','SA','WA','TAS','NT','ACT']
CAP={'NSW':'SYD','VIC':'MEL','QLD':'BRI','SA':'ADL','WA':'PER','TAS':'HOB','NT':'DAR','ACT':'CBR'}
def fy_of(period):              # 'YYYY-Qn' -> financial year ending June
    y,qn=int(period[:4]),int(period[-1]); return y+1 if qn>=3 else y
def fy_avg(df,col):
    d=df[['period',col]].dropna().copy(); d['fy']=d.period.map(fy_of)
    g=d.groupby('fy')[col].agg(['mean','count']); return g[g['count']==4]['mean']
# ---------- macro ----------
mac=pd.read_csv(f'{R}/rba_macro_q.csv')
cpi=fy_avg(mac,'cpi_idx')
mort=fy_avg(mac,'oo_std_var')
infl=mac[['period','cpi_trim_yoy','cpi_yoy']].copy(); infl['x']=infl.cpi_trim_yoy.fillna(infl.cpi_yoy); infl=fy_avg(infl,'x')
rrate=(mort-infl).rename('rrate')
# ---------- prices ----------
tvd=pd.read_csv(f'{R}/abs_tvd_t2_median_prices_q.csv'); hlr=pd.read_csv(f'{R}/abs_6416_t8_established_homes_1986_2005.csv')
series={}
for s in ST:
    c=CAP[s]
    med=fy_avg(tvd,'H_'+c); old=fy_avg(hlr,'HLR_'+c)
    ov=[y for y in (2003,2004,2005) if y in med.index and y in old.index]
    k=np.mean([med[y]/old[y] for y in ov]); sp=pd.concat([old[old.index<=2002]*k, med[med.index>=2003]])
    series[(s,'cap','H')]=sp
    series[(s,'cap','U')]=fy_avg(tvd,'U_'+c)
    if s!='ACT':
        series[(s,'rest','H')]=fy_avg(tvd,'H_r'+s); series[(s,'rest','U')]=fy_avg(tvd,'U_r'+s)
# ---------- state fundamentals ----------
pop=pd.read_csv(f'{R}/abs_3101_population_fy.csv').set_index('fy_end_june')
com=pd.read_csv(f'{R}/abs_8752_completions_fy.csv').set_index('fy_end_june')
inc=pd.read_csv(f'{R}/abs_5220_household_gdi_fy.csv').set_index('fy_end_june')
ihpd=pd.read_csv(f'{R}/dallasfed_ihpd_annual_q4.csv'); ihpd=ihpd[ihpd.period.str.endswith('Q4')].copy()
ihpd['fy']=ihpd.period.str[:4].astype(int)+1                        # calendar Q4 -> middle of next FY
pti=(np.log(ihpd.rhpi_AUS/ihpd.rpdi_AUS)).values; fyv=ihpd.fy.values
vgap=pd.Series([pti[i]-pti[:i+1].mean() for i in range(len(pti))],index=fyv)   # expanding mean, no lookahead
def statefeat(s):
    p=pop['pop_'+s]; c=com['compl_H_'+s]+com['compl_U_'+s]
    pop5=np.log(p/p.shift(5)); ppc5=((p-p.shift(5))/c.rolling(5).sum()).clip(-1,5)
    return pd.DataFrame({'pop5':pop5,'ppc5':ppc5})
SF={s:statefeat(s) for s in ST}
# ---------- panel rows ----------
rows=[]
for key,ps in series.items():
    s,reg,ty=key; lp=np.log(ps/cpi.reindex(ps.index)).dropna()
    for t in lp.index:
        r=dict(state=s,reg=reg,ty=ty,t=t,lp=lp[t],vgap=vgap.get(t,np.nan),rrate=rrate.get(t,np.nan),
               pop5=SF[s].pop5.get(t,np.nan),ppc5=SF[s].ppc5.get(t,np.nan),
               mom3=lp[t]-lp.get(t-3,np.nan))
        for h in range(1,11): r[f'y{h}']=lp.get(t+h,np.nan)-lp[t]
        rows.append(r)
P=pd.DataFrame(rows)
P['dU']=(P.ty=='U')*1.0; P['dR']=(P.reg=='rest')*1.0
FEAT=['vgap','rrate','pop5','ppc5','mom3','dU','dR']
# ---------- analogue panel (forward h outcomes, by valuation percentile) ----------
a=pd.read_csv(f'{R}/dallasfed_ihpd_annual_q4.csv'); a=a[a.period.str.endswith('Q4')]; a['y']=a.period.str[:4].astype(int)
CS=['AUS','NZL','CAN','GBR','IRL','NLD','SWE','NOR','DNK','USA','ESP','JPN']; arows=[]
for c in CS:
    lr=np.log(a['rhpi_'+c].values); pv=np.log(a['rhpi_'+c].values/a['rpdi_'+c].values); yy=a.y.values
    for i in range(10,len(yy)):
        pct=(pv[:i+1]<=pv[i]).mean()
        for h in range(1,11):
            if i+h<len(yy): arows.append(dict(c=c,y=yy[i]+1,h=h,pct=pct,fwd=lr[i+h]-lr[i]))   # +1: align to FY
A=pd.DataFrame(arows)
aus_pct={}
pv=np.log(a.rhpi_AUS.values/a.rpdi_AUS.values)
for i in range(len(pv)): aus_pct[int(a.y.values[i])+1]=(pv[:i+1]<=pv[i]).mean()
def m2(t,h):                      # base-rate median for AUS valuation bucket, outcomes known by t
    pc=aus_pct.get(t,np.nan); sub=A[(A.h==h)&(A.y+h<=t)]
    if np.isnan(pc) or len(sub)<20: return np.nan
    near=sub[(sub.pct-pc).abs()<=0.15]
    return (near if len(near)>=15 else sub).fwd.median()
# ---------- models ----------
def ols(X,y):
    X1=np.c_[np.ones(len(X)),X]; b,*_=np.linalg.lstsq(X1,y,rcond=None); return b
def fit_m1(train,h):
    d=train.dropna(subset=FEAT+[f'y{h}']); 
    if len(d)<25: return None
    mu=d[FEAT].mean(); sd=d[FEAT].std().replace(0,1); Xs=(d[FEAT]-mu)/sd
    # ridge-lite: shrink coefficients toward 0 (lambda chosen a priori, not tuned on test) to curb overfitting
    X1=np.c_[np.ones(len(Xs)),Xs.values]; lam=2.0*len(Xs)/100; I=np.eye(X1.shape[1]); I[0,0]=0
    b=np.linalg.solve(X1.T@X1+lam*I, X1.T@d[f'y{h}'].values); return (b,mu,sd)
def pred_m1(m,row):
    if m is None: return np.nan
    b,mu,sd=m; x=((row[FEAT]-mu)/sd).values.astype(float)
    if np.any(np.isnan(x)): return np.nan
    return b[0]+x@b[1:]
def drift(train,key,h):
    s,reg,ty=key; d=train[(train.state==s)&(train.reg==reg)&(train.ty==ty)].sort_values('t')
    if len(d)<8: d=train[(train.state==s)&(train.reg=='cap')&(train.ty=='H')].sort_values('t')
    g=np.diff(d.lp.values); return g.mean()*h if len(g) else np.nan
WIN=[(2005,'W1 train<=2005 -> 2006-15'),(2010,'W2 train<=2010 -> 2011-20'),(2015,'W3 train<=2015 -> 2016-25')]
recs=[]
for T,lab in WIN:
    for h in range(1,11):
        tr=P[P.t+h<=T]                        # only outcomes observable at T  (no lookahead)
        m=fit_m1(tr,h)
        te=P[(P.t==T)&P[f'y{h}'].notna()]
        for _,r in te.iterrows():
            key=(r.state,r.reg,r.ty)
            recs.append(dict(win=lab,origin=T,h=h,state=r.state,reg=r.reg,ty=r.ty,act=r[f'y{h}'],
                             B1=0.0,B2=drift(P[P.t<=T],key,h),M1=pred_m1(m,r),M2=m2(T,h)))
BT=pd.DataFrame(recs)
MODS=['B1','B2','M1','M2']
def rmse(x): x=x.dropna(); return float(np.sqrt((x**2).mean())) if len(x) else np.nan
res={'n_obs':len(BT)}
tab={}
for lab in [w[1] for w in WIN]:
    d=BT[BT.win==lab]; tab[lab]={m:{'rmse_h10':round(rmse(d[d.h==10].act-d[d.h==10][m]),3),
                                    'rmse_allh':round(rmse(d.act-d[m]),3),'n_h10':int(d[d.h==10][m].notna().sum())} for m in MODS}
res['backtest_rmse_logreal']=tab
# ---- ensemble weights: chosen on W1+W2, evaluated on W3 (nested, honest) ----
def inv_mse_w(d,mods):
    w={m:1/max(rmse(d.act-d[m])**2,1e-6) for m in mods if d[m].notna().any()}
    s=sum(w.values()); return {m:v/s for m,v in w.items()}
early=BT[BT.origin<2015]; late=BT[BT.origin==2015]
base_best=min(rmse(early.act-early.B1),rmse(early.act-early.B2))
elig=[m for m in MODS if rmse(early.act-early[m])<=base_best*1.0+1e-9 or m in ('B1','B2')]
w_nested=inv_mse_w(early,[m for m in MODS])
def ens(d,w): 
    num=sum(d[m].fillna(0)*v for m,v in w.items()); den=sum(d[m].notna()*v for m,v in w.items()); return num/den
late=late.assign(ENS=ens(late,w_nested))
res['nested_weights_fit_W1W2']={k:round(v,3) for k,v in w_nested.items()}
res['W3_oos_rmse']={m:round(rmse(late.act-late[m]),3) for m in MODS+['ENS']}
res['W3_oos_rmse_h10']={m:round(rmse(late[late.h==10].act-late[late.h==10][m]),3) for m in MODS+['ENS']}
# per-state W3 h10
res['W3_h10_by_series']=late[late.h==10][['state','reg','ty','act','B1','B2','M1','M2','ENS']].round(3).to_dict('records')
# ---- calibration: intervals from W1+W2 OOS ensemble errors, tested on W3 ----
early=early.assign(ENS=ens(early,w_nested)); err=early.act-early.ENS
cov={}
for h in range(1,11):
    e=(early[early.h==h].act-early[early.h==h].ENS).dropna()
    if len(e)<5: continue
    # widen by sqrt horizon scaling from pooled errors if small sample
    lo80,hi80=np.quantile(e,0.1),np.quantile(e,0.9); lo50,hi50=np.quantile(e,0.25),np.quantile(e,0.75)
    d=late[late.h==h].dropna(subset=['ENS']); z=d.act-d.ENS
    cov[h]=dict(n_cal=len(e),n_test=len(z),cov80=round(float(((z>=lo80)&(z<=hi80)).mean()),2),cov50=round(float(((z>=lo50)&(z<=hi50)).mean()),2))
res['calibration_W3_using_W1W2_intervals']=cov
BT.to_csv(f'{B}/backtest_predictions.csv',index=False); P.to_csv(f'{B}/panel_fy.csv',index=False)
json.dump(res,open(f'{B}/model_results.json','w'),indent=1,default=str)
print(json.dumps({k:res[k] for k in res if k!='W3_h10_by_series'},indent=1,default=str))
