#!/usr/bin/env python3
# "The pick is parabolic / way overbought (DELL)." Does buying the MOST stretched
# momentum name hurt forward return / drawdown? And does an extension cap help?
# extension = price / 200d MA - 1  (how far above the trend line the pick is).
import json, statistics as stt
P=json.load(open('backtests/deep-panel.json'))
EXCL={'SPY','AGG','BTC-USD'}
T=[t for t in sorted(P) if t not in EXCL]
dates=sorted(P['SPY'].keys())
COL={t:[P[t].get(d) for d in dates] for t in T}
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
def worst_dd(cl,i,H):
    e=cl[i]
    if e is None or e<=0:return None
    lo=None
    for k in range(i+1,min(i+H+1,len(cl))):
        v=cl[k]
        if v is None:continue
        r=v/e-1; lo=r if lo is None or r<lo else lo
    return lo
H=126;COST=0.003;START=1260
def ext(cl,i):
    m=sma(cl,200,i); return (cl[i]/m-1) if (m and cl[i]) else None
def uptrend(cl,i):
    m=sma(cl,200,i);return m is not None and cl[i] is not None and cl[i]>m
def pick(i,cap):
    best=None;bv=None
    for t in T:
        cl=COL[t]
        if not uptrend(cl,i):continue
        e=ext(cl,i)
        if cap is not None and (e is None or e>cap):continue
        v=ret(cl,i,126)
        if v is None:continue
        if bv is None or v>bv:bv=v;best=t
    return best
# 1) bucket the UNCAPPED momentum pick by its extension
i=START;N=len(dates);recs=[]
while i+H<N:
    t=pick(i,None)
    if t:
        e=ext(COL[t],i); r=ret(COL[t],i+H,H); dd=worst_dd(COL[t],i,H)
        if None not in (e,r,dd): recs.append((e,r-COST,dd))
    i+=21
recs.sort(key=lambda x:x[0])
n=len(recs);tercile=n//3
def summ(rows):
    e=[x[0] for x in rows];r=[x[1] for x in rows];d=[x[2] for x in rows]
    return (stt.median(e)*100, stt.median(r)*100,(sum(r)/len(r))*100, stt.median(d)*100,
            sum(1 for x in r if x>0)/len(r)*100)
print('MOMENTUM PICK bucketed by extension (dist above 200d MA) — 6-mo forward')
for lbl,rows in [('LEAST stretched 1/3',recs[:tercile]),
                 ('middle 1/3',recs[tercile:2*tercile]),
                 ('MOST stretched 1/3',recs[2*tercile:])]:
    me,mr,ar,md,w=summ(rows)
    print('  %-20s  ext~%+5.0f%%  medRet %+6.1f%%  meanRet %+6.1f%%  worstDip %+6.1f%%  win %.0f%%'%(lbl,me,mr,ar,md,w))

# 2) does an EXTENSION CAP improve the strategy overall? (beat-EW both halves too)
def ewavg(i,H):
    rs=[ret(COL[t],i+H,H) for t in T];rs=[x for x in rs if x is not None]
    return sum(rs)/len(rs) if rs else None
print('\nEXTENSION CAP on the momentum pick (skip names >cap above 200d MA):')
for cap in [None,1.00,0.60,0.40,0.25]:
    i=START;rows=[]
    while i+H<N:
        t=pick(i,cap)
        if t:
            r=ret(COL[t],i+H,H);dd=worst_dd(COL[t],i,H);e=ewavg(i,H)
            if None not in (r,dd,e): rows.append((i,r-COST,dd,e))
        i+=21
    mid=rows[len(rows)//2][0]
    h1=[r-e for d,r,dd,e in rows if d<mid];h2=[r-e for d,r,dd,e in rows if d>=mid]
    rr=[r for _,r,_,_ in rows];dd=[d for _,_,d,_ in rows]
    beat=sum(1 for _,r,_,e in rows if r>e)/len(rows)
    lbl='none' if cap is None else '%.0f%%'%(cap*100)
    print('  cap %-5s n=%d  medRet %+6.1f%%  worstDip %+6.1f%%  win %.0f%%  beatEW %.0f%%  (H1>EW %s H2>EW %s)'
          %(lbl,len(rows),stt.median(rr)*100,stt.median(dd)*100,
            sum(1 for x in rr if x>0)/len(rr)*100, beat*100,
            'Y' if sum(h1)/len(h1)>0 else 'n','Y' if sum(h2)/len(h2)>0 else 'n'))
