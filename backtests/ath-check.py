#!/usr/bin/env python3
# "Isn't this just buying all-time highs?" — measure it honestly.
# A = current rule: uptrend name with highest 6-mo return (buys STRENGTH).
# B = the "don't buy the top" alternative: uptrend name furthest BELOW its 1-yr
#     high (buy the biggest DIP that's still in an uptrend).
# For each: forward 6-mo return (net 15bps/side) AND worst intra-hold drawdown
# (min close over the next 126 days / entry - 1). Plus A's distance-from-high at entry.
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
def max_over(cl,i,b):   # max close in [i-b+1 .. i]
    if i-b+1<0:return None
    vals=[cl[k] for k in range(i-b+1,i+1) if cl[k] is not None]
    return max(vals) if vals else None
def worst_dd(cl,i,H):   # worst close/entry-1 over next H days
    e=cl[i]
    if e is None or e<=0:return None
    lo=None
    for k in range(i+1,min(i+H+1,len(cl))):
        v=cl[k]
        if v is None:continue
        r=v/e-1
        lo=r if lo is None or r<lo else lo
    return lo
H=126;COST=0.003;START=1260
def uptrend(cl,i):
    m=sma(cl,200,i);return m is not None and cl[i] is not None and cl[i]>m
def pickA(i):  # highest 6-mo return in uptrend
    best=None;bv=None
    for t in T:
        cl=COL[t]
        if not uptrend(cl,i):continue
        v=ret(cl,i,126)
        if v is None:continue
        if bv is None or v>bv:bv=v;best=t
    return best
def pickB(i):  # in uptrend, furthest below its 252-day high (biggest dip)
    best=None;bv=None
    for t in T:
        cl=COL[t]
        if not uptrend(cl,i):continue
        hi=max_over(cl,i,252)
        if not hi:continue
        v=cl[i]/hi-1   # <=0, more negative = deeper below high
        if bv is None or v<bv:bv=v;best=t
    return best
rowsA=[];rowsB=[];distA=[];rowsEW=[]
i=START;N=len(dates)
while i+H<N:
    a=pickA(i);b=pickB(i)
    if a:
        r=ret(COL[a],i+H,H);dd=worst_dd(COL[a],i,H)
        hi=max_over(COL[a],i,252); d=(COL[a][i]/hi-1) if hi else None
        if r is not None and dd is not None: rowsA.append((r-COST,dd)); distA.append(d)
    if b:
        r=ret(COL[b],i+H,H);dd=worst_dd(COL[b],i,H)
        if r is not None and dd is not None: rowsB.append((r-COST,dd))
    # EW null
    rs=[ret(COL[t],i+H,H) for t in T]; rs=[x for x in rs if x is not None]
    dds=[worst_dd(COL[t],i,H) for t in T]; dds=[x for x in dds if x is not None]
    if rs and dds: rowsEW.append((sum(rs)/len(rs), sum(dds)/len(dds)))
    i+=21
def rep(name,rows):
    rr=[r for r,_ in rows]; dd=[d for _,d in rows]
    print('  %-26s n=%d  medRet %+6.1f%%  meanRet %+6.1f%%  median worst-dip %+6.1f%%  win %.0f%%'
          %(name,len(rows),stt.median(rr)*100,(sum(rr)/len(rr))*100,stt.median(dd)*100,
            sum(1 for x in rr if x>0)/len(rr)*100))
print('6-MONTH HOLD — buying STRENGTH vs buying the DIP (survivor sample, costs on)')
rep('A: highest momentum (ATH-ish)',rowsA)
rep('B: biggest dip in uptrend',rowsB)
rep('EW: average stock',rowsEW)
d=[x for x in distA if x is not None]
print('\nHow "ATH" is pick A really? distance below its 1-yr high at entry:')
print('  median %+.1f%%   mean %+.1f%%   at-the-high(<2%% below): %.0f%% of picks   >10%% below: %.0f%%'
      %(stt.median(d)*100, (sum(d)/len(d))*100,
        sum(1 for x in d if x>-0.02)/len(d)*100, sum(1 for x in d if x<-0.10)/len(d)*100))
