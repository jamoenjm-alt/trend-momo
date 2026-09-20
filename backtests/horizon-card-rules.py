#!/usr/bin/env python3
# Validate the EXACT per-card live rules. Each must beat the equal-weight null in
# BOTH halves to earn a non-grey tier. Report beat-EW%, median excess, win%.
import json,statistics as stt
P=json.load(open('backtests/deep-panel.json'))
EXCL={'SPY','AGG','BTC-USD'}
T=[t for t in sorted(P) if t not in EXCL]
dates=sorted(P['SPY'].keys())
COL={t:[P[t].get(d) for d in dates] for t in T}
SPY=[P['SPY'].get(d) for d in dates]
MA=[(10,3,'c'),(15,5,'c'),(42,10,'s'),(50,15,'s'),(63,21,'s'),(84,21,'l'),(126,42,'l'),(168,42,'l'),(200,50,'a'),(252,63,'a')]
def sma(cl,w,i):
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
def allInd(cl,i):
    price=cl[i]
    if price is None:return None
    vals=[]
    for slow,fast,g in MA:
        sM=sma(cl,slow,i);fM=sma(cl,fast,i)
        if sM is not None:vals.append(1 if price>sM else -1)
        if fM is not None and sM is not None:vals.append(1 if fM>sM else -1)
    return sum(vals)/len(vals) if vals else None
def vstable(cl,i):
    def rk(lb):
        v=allInd(cl,i-lb)
        return None if v is None else (0 if v>0.6 else 1 if v>0.2 else 2 if v>-0.2 else 3 if v>-0.6 else 4)
    seq=[rk(x) for x in (30,20,10,0)];seq=[x for x in seq if x is not None]
    if len(seq)<2:return False
    return sum(1 for j in range(1,len(seq)) if seq[j]!=seq[j-1])==0
# card rules: (key, hold_days, ranker, need_stable, label)
def ranker_mom(lb):
    return lambda cl,i: ret(cl,i,lb)
def ranker_dist(cl,i):
    m=sma(cl,200,i); return (cl[i]/m-1) if (m and cl[i]) else None
CARDS=[
 ('1wk',5,   ranker_dist,      False,'trend distance (price vs 200d)'),
 ('1mo',21,  ranker_mom(63),   False,'3-month momentum, uptrend only'),
 ('6mo',126, ranker_mom(126),  False,'6-month momentum, uptrend only'),
 ('1yr',252, ranker_mom(126),  True, '6-month momentum, stable uptrend'),
 ('5yr',1260,ranker_mom(252),  True, '12-month momentum, stable uptrend'),
]
def pick(i,rk,ns):
    best=None;bv=None
    for t in T:
        cl=COL[t]
        if cl[i] is None:continue
        m=sma(cl,200,i)
        if not m or cl[i]<=m:continue
        if ns and not vstable(cl,i):continue
        v=rk(cl,i)
        if v is None:continue
        if bv is None or v>bv:bv=v;best=t
    return best
def ewavg(i,H):
    vs=[ret(COL[t],i+H,H) for t in T];vs=[v for v in vs if v is not None]
    return sum(vs)/len(vs) if vs else None
COST=0.003;START=1260
print('%-4s %-34s %5s %6s %6s %7s %6s %5s'%('hold','rule','n','H1>EW','H2>EW','beatEW','medEXC','win'))
res={}
for k,H,rk,ns,lab in CARDS:
    i=START;N=len(dates);rows=[]
    while i+H<N:
        t=pick(i,rk,ns)
        if t:
            r=ret(COL[t],i+H,H);e=ewavg(i,H)
            if r is not None and e is not None: rows.append((i,r-COST,e))
        i+=21
    n=len(rows);mid=rows[n//2][0]
    h1=[(r-e) for d,r,e in rows if d<mid];h2=[(r-e) for d,r,e in rows if d>=mid]
    beatEW=sum(1 for d,r,e in rows if r>e)/n
    medEXC=stt.median([r-e for d,r,e in rows]);win=sum(1 for d,r,e in rows if r>0)/n
    h1ok=sum(h1)/len(h1)>0; h2ok=sum(h2)/len(h2)>0
    res[k]=(beatEW,medEXC,win,h1ok and h2ok)
    print('%-4s %-34s %5d %6s %6s %5.0f%% %+6.1f%% %4.0f%%'%(k,lab,n,'Y' if h1ok else 'n','Y' if h2ok else 'n',beatEW*100,medEXC*100,win*100))
print('\nTIER (from beatEW, bias-robust):')
for k in res:
    be,me,w,ok=res[k]
    tier='green' if (be>=0.60 and ok) else 'amber' if (be>=0.55 and ok) else 'grey'
    print('  %-4s beatEW %.0f%% medExcess %+.1fpp -> %s'%(k,be*100,me*100,tier))
