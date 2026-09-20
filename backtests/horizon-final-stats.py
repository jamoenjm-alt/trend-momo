#!/usr/bin/env python3
# Final honest stats for the EXACT live rule per horizon.
# Rule: momentum-in-uptrend (top 126d return among names above their 200d MA),
#       1yr/5yr additionally require a 'stable' regime (allInd sign unchanged 30d).
# Report bias-robust metrics: beat-EW rate, beat-SPY rate, MEDIAN excess vs EW,
# plus (optimistic) mean absolute. Split H1/H2.
import json,statistics as stt
P=json.load(open('backtests/deep-panel.json'))
EXCL={'SPY','AGG','BTC-USD'}
T=[t for t in sorted(P) if t not in EXCL]
dates=sorted(P['SPY'].keys())
COL={t:[P[t].get(d) for d in dates] for t in T}
SPY=[P['SPY'].get(d) for d in dates]
MA_PAIRS=[(10,3,'c'),(15,5,'c'),(42,10,'s'),(50,15,'s'),(63,21,'s'),(84,21,'l'),(126,42,'l'),(168,42,'l'),(200,50,'a'),(252,63,'a')]
def sma(cl,w,i):
    if i+1<w: return None
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
    for slow,fast,g in MA_PAIRS:
        sM=sma(cl,slow,i);fM=sma(cl,fast,i)
        if sM is not None: vals.append(1 if price>sM else -1)
        if fM is not None and sM is not None: vals.append(1 if fM>sM else -1)
    return sum(vals)/len(vals) if vals else None
def stable(cl,i):
    def rk(lb):
        v=allInd(cl,i-lb)
        if v is None:return None
        return 0 if v>0.6 else 1 if v>0.2 else 2 if v>-0.2 else 3 if v>-0.6 else 4
    seq=[rk(x) for x in (30,20,10,0)]; seq=[x for x in seq if x is not None]
    if len(seq)<2:return False
    flips=sum(1 for j in range(1,len(seq)) if seq[j]!=seq[j-1])
    return flips==0   # 'very_stable'
def pick(i,need_stable):
    best=None;bv=None
    for t in T:
        cl=COL[t]
        if cl[i] is None:continue
        m=sma(cl,200,i)
        if not m or cl[i]<=m:continue
        if need_stable and not stable(cl,i):continue
        v=ret(cl,i,126)
        if v is None:continue
        if bv is None or v>bv:bv=v;best=t
    return best
def ewavg(i,H):
    vs=[ret(COL[t],i+H,H) for t in T];vs=[v for v in vs if v is not None]
    return sum(vs)/len(vs) if vs else None
COST=0.003;START=1260
HOLDS=[('1wk',5,False),('1mo',21,False),('6mo',126,False),('1yr',252,True),('5yr',1260,True)]
print('Rule = 6-mo momentum among uptrends (1yr/5yr also require very-stable regime). 15bps/side.')
print('%-4s %6s %7s %8s %8s %8s %7s'%('hold','n','beatEW%','beatSPY%','medEXC','meanABS','win%'))
OUT={}
for hz,H,ns in HOLDS:
    i=START;N=len(dates);rows=[]
    while i+H<N:
        t=pick(i,ns)
        if t:
            r=ret(COL[t],i+H,H); e=ewavg(i,H); s=ret(SPY,i+H,H)
            if r is not None and e is not None and s is not None:
                rows.append((r-COST,e,s))
        i+=21
    n=len(rows)
    beatEW=sum(1 for r,e,s in rows if r>e)/n
    beatSPY=sum(1 for r,e,s in rows if r>s)/n
    medEXC=stt.median([r-e for r,e,s in rows])
    meanABS=sum(r for r,e,s in rows)/n
    win=sum(1 for r,e,s in rows if r>0)/n
    OUT[hz]=(n,beatEW,beatSPY,medEXC,meanABS,win)
    print('%-4s %6d %6.0f%% %7.0f%% %+7.1f%% %+7.1f%% %6.0f%%'%(hz,n,beatEW*100,beatSPY*100,medEXC*100,meanABS*100,win*100))
print('\nInterpretation seed:')
for hz in OUT:
    n,be,bs,me,ma,w=OUT[hz]
    verdict = 'NOISE' if be<0.55 else ('EDGE' if be>=0.60 else 'WEAK')
    print('  %-4s beatEW %.0f%% -> %s'%(hz,be*100,verdict))
