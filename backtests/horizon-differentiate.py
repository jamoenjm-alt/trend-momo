#!/usr/bin/env python3
# Do DIFFERENT signals genuinely win at different horizons (so cards show
# different names), or is it really one signal? Pre-registered menu, H1/H2 split,
# 15bps/side, benchmark = equal-weight null. A signal "qualifies" only if it beats
# EW in BOTH halves. Also report how often its pick differs from 126d-momentum.
import json, statistics as stt
P=json.load(open('backtests/deep-panel.json'))
EXCL={'SPY','AGG','BTC-USD'}
T=[t for t in sorted(P) if t not in EXCL]
dates=sorted(P['SPY'].keys())
COL={t:[P[t].get(d) for d in dates] for t in T}
def sma(cl,i,w):
    if i+1<w:return None
    s=0.0
    for k in range(i-w+1,i+1):
        v=cl[k]
        if v is None:return None
        s+=v
    return s/w
def ret(cl,i,b):
    if i-b<0:return None
    a=cl[i-b];c=cl[i]
    if a is None or c is None or a<=0:return None
    return c/a-1
def vol(cl,i,w=126):
    rs=[]
    for k in range(i-w+1,i+1):
        a=cl[k-1];b=cl[k]
        if a and b and a>0: rs.append(b/a-1)
    return stt.pstdev(rs) if len(rs)>5 else None
def runlen(cl,i):  # consecutive days above 200MA
    n=0
    for k in range(i,max(i-400,199),-1):
        m=sma(cl,k,200)
        if m is None or cl[k] is None or cl[k]<=m: break
        n+=1
    return n
def uptrend(cl,i):
    m=sma(cl,i,200); return m is not None and cl[i] is not None and cl[i]>m
def ext(cl,i):
    m=sma(cl,i,200); return (cl[i]/m-1) if (m and cl[i]) else None

def make(kind):
    def pick(i):
        best=None;bv=None
        for t in T:
            cl=COL[t]
            if not uptrend(cl,i): continue
            v=None;pref='high'
            if kind=='mom126': v=ret(cl,i,126)
            elif kind=='mom63': v=ret(cl,i,63)
            elif kind=='mom252': v=ret(cl,i,252)
            elif kind=='rev5': v=ret(cl,i,5); pref='low'
            elif kind=='mom_mod':
                e=ext(cl,i)
                if e is not None and e<=0.35: v=ret(cl,i,126)
            elif kind=='lowvol': vv=vol(cl,i); v=(-vv) if vv is not None else None
            elif kind=='stable': v=runlen(cl,i)
            elif kind=='dist': v=ext(cl,i)
            if v is None: continue
            if bv is None or (pref=='high' and v>bv) or (pref=='low' and v<bv): bv=v;best=t
        return best
    return pick
def ewnull(i,H):
    rs=[ret(COL[t],i+H,H) for t in T]; rs=[x for x in rs if x is not None]
    return sum(rs)/len(rs) if rs else None
COST=0.003;START=1260
HZ=[('1mo',21,['mom126','mom63','rev5','dist','lowvol']),
    ('1yr',252,['mom126','mom252','mom_mod','lowvol','stable']),
    ('5yr',1260,['mom126','mom252','mom_mod','lowvol','stable'])]
mom=make('mom126')
for hz,H,cands in HZ:
    print('\n### %s hold'%hz)
    print('  %-9s %7s %7s %7s %6s %8s'%('signal','H1exc','H2exc','medRet','beatEW','diff%'))
    for k in cands:
        pk=make(k); i=START;N=len(dates)
        rows=[];diff=0;tot=0
        while i+H<N:
            t=pk(i); e=ewnull(i,H)
            if t and e is not None:
                r=ret(COL[t],i+H,H)
                if r is not None:
                    rows.append((i,r-COST,e))
                    mt=mom(i); tot+=1
                    if mt!=t: diff+=1
            i+=21
        n=len(rows);mid=rows[n//2][0]
        h1=[r-e for d,r,e in rows if d<mid];h2=[r-e for d,r,e in rows if d>=mid]
        beat=sum(1 for d,r,e in rows if r>e)/n
        h1e=sum(h1)/len(h1);h2e=sum(h2)/len(h2)
        medR=stt.median([r for _,r,_ in rows])
        q='Y' if (h1e>0 and h2e>0) else '.'
        print('  %-9s %+6.1f%% %+6.1f%% %+6.1f%% %5.0f%% %s  %4.0f%%'%(k,h1e*100,h2e*100,medR*100,beat*100,q,(diff/tot*100 if tot else 0)))
    print('  (diff% = how often this signal picks a DIFFERENT name than 126d-momentum)')
