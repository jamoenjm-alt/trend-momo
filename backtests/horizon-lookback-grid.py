#!/usr/bin/env python3
# Does the BEST momentum lookback change with HOLD length? (grid test)
# If yes -> honest per-horizon differentiation. If no -> one rule; say so.
import json
P=json.load(open('backtests/deep-panel.json'))
EXCL={'SPY','AGG','BTC-USD'}
T=[t for t in sorted(P) if t not in EXCL]
dates=sorted(P['SPY'].keys())
COL={t:[P[t].get(d) for d in dates] for t in T}
SPY=[P['SPY'].get(d) for d in dates]
def sma(cl,w,i):
    if i+1<w: return None
    s=0.0
    for k in range(i-w+1,i+1):
        v=cl[k]
        if v is None: return None
        s+=v
    return s/w
def ret(cl,i,b):
    if i-b<0: return None
    a=cl[i-b]; c=cl[i]
    if a is None or c is None or a<=0: return None
    return c/a-1
def pick_mom(i,lb):
    # highest lb-day return AND above 200d MA (momentum-in-uptrend)
    best=None;bv=None
    for t in T:
        cl=COL[t]
        if cl[i] is None: continue
        m=sma(cl,200,i)
        if not m or cl[i]<=m: continue
        v=ret(cl,i,lb)
        if v is None: continue
        if bv is None or v>bv: bv=v;best=t
    return best
COST=0.003
START=1260
def test(lb,H):
    rows=[];i=START;N=len(dates)
    while i+H<N:
        t=pick_mom(i,lb)
        if t:
            r=ret(COL[t],i+H,H)
            if r is not None: rows.append((i,r-COST))
        i+=21
    if not rows: return None
    mid=rows[len(rows)//2][0]
    h1=[r for d,r in rows if d<mid];h2=[r for d,r in rows if d>=mid];fu=[r for _,r in rows]
    m=lambda x:sum(x)/len(x)
    wr=sum(1 for _,r in rows if r>0)/len(rows)
    return (m(h1),m(h2),m(fu),wr,len(rows))
def ewnull(H):
    rows=[];i=START;N=len(dates)
    while i+H<N:
        vs=[ret(COL[t],i+H,H) for t in T]; vs=[v for v in vs if v is not None]
        if vs: rows.append((i,sum(vs)/len(vs)))
        i+=21
    mid=rows[len(rows)//2][0]
    h1=[r for d,r in rows if d<mid];h2=[r for d,r in rows if d>=mid]
    return sum(h1)/len(h1),sum(h2)/len(h2)
LBS=[21,42,63,126,168,252]
HOLDS=[('1wk',5),('1mo',21),('6mo',126),('1yr',252),('5yr',1260)]
print('MOMENTUM-IN-UPTREND: best lookback per hold (FULL mean %, * = beats EW both halves)')
print('%-5s'%'hold','  '.join('%6dd'%lb for lb in LBS))
for hz,H in HOLDS:
    e1,e2=ewnull(H)
    cells=[]
    best=None
    for lb in LBS:
        r=test(lb,H)
        if r is None: cells.append('   -  ');continue
        h1,h2,fu,wr,n=r
        beat = h1>e1 and h2>e2
        cells.append(('%+6.1f'%(fu*100))+('*' if beat else ' '))
        if beat and (best is None or fu>best[1]): best=(lb,fu,wr)
    tag = ('  -> best lb=%dd (%.0f%% full, win %.0f%%)'%(best[0],best[1]*100,best[2]*100)) if best else '  -> none beat EW'
    print('%-5s'%hz,'  '.join(cells),tag)
