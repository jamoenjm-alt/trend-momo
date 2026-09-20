#!/usr/bin/env python3
# ============================================================================
# EXTENSION BASE-RATE STUDY (descriptive, not a signal)
# Q: when a megacap is X% above its 200-day MA, what is the base rate & size of a
#    pullback over the next 63 / 126 trading days, and how long until it reverts
#    to the 200MA? Also condition on RSI(14) and on how long it's been extended.
# Universe: deep-panel survivors (bias noted). Every trading day with >=1yr fwd
#    data is one observation (overlapping -> point estimates fine, CIs not).
# ============================================================================
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
def rsi(cl,i,w=14):
    if i<w:return None
    gains=0.0;losses=0.0;m=0
    for k in range(i-w+1,i+1):
        a=cl[k-1];b=cl[k]
        if a is None or b is None:return None
        ch=b-a
        if ch>=0:gains+=ch
        else:losses-=ch
        m+=1
    if m==0:return None
    ag=gains/w;al=losses/w
    if al==0:return 100.0
    rs=ag/al
    return 100-100/(1+rs)
def worst_dip(cl,i,H):
    e=cl[i]
    if e is None or e<=0:return None
    lo=0.0
    for k in range(i+1,min(i+H+1,len(cl))):
        v=cl[k]
        if v is None:continue
        r=v/e-1
        if r<lo:lo=r
    return lo
def fwd_ret(cl,i,H):
    if i+H>=len(cl):return None
    a=cl[i];b=cl[i+H]
    if a is None or b is None or a<=0:return None
    return b/a-1
def days_to_200(cl,i,cap=252):
    # trading days until price closes at/below its (contemporaneous) 200MA
    for k in range(i+1,min(i+cap+1,len(cl))):
        m=sma(cl,k,200)
        if m is None or cl[k] is None:continue
        if cl[k]<=m:return k-i
    return None   # didn't revert within cap

# ---- gather observations: only when stock is ABOVE its 200MA (an uptrend) ----
obs=[]  # (ext, rsi14, run_days_above_200, dip63, dip126, ret63, ret126, d2rev)
for t in T:
    cl=COL[t]
    run=0
    for i in range(len(cl)):
        m=sma(cl,i,200)
        if m is None or cl[i] is None:
            run=0; continue
        above = cl[i]>m
        run = run+1 if above else 0
        if not above: continue
        if i+126>=len(cl): continue
        ext=cl[i]/m-1
        obs.append((ext, rsi(cl,i), run,
                    worst_dip(cl,i,63), worst_dip(cl,i,126),
                    fwd_ret(cl,i,63), fwd_ret(cl,i,126),
                    days_to_200(cl,i,252)))
print('observations (stock above its 200MA, >=126d fwd):',len(obs))

# ---- A) extension distribution ----
exts=sorted(x[0] for x in obs)
def pct(a,p): return a[int(p/100*(len(a)-1))]
print('\nA) How far above the 200MA do megacaps trade? (percentiles of extension)')
for p in [10,25,50,75,90,95,99]:
    print('   p%-2d  %+6.1f%%'%(p,pct(exts,p)*100))

# ---- B) forward pullback by extension bucket ----
BUCK=[(-1,0.10),(0.10,0.20),(0.20,0.35),(0.35,0.50),(0.50,0.80),(0.80,99)]
def med(x): return stt.median(x)*100 if x else float('nan')
print('\nB) Forward outcomes by extension bucket (next 63 trading days ~3 months)')
print('   %-14s %6s %8s %8s %8s %9s'%('extension','n','medDip','P(>=10%dip)','P(>=20%)','medRet'))
for lo,hi in BUCK:
    g=[x for x in obs if lo<x[0]<=hi]
    if not g:continue
    dips=[x[3] for x in g if x[3] is not None]
    p10=sum(1 for d in dips if d<=-0.10)/len(dips)*100
    p20=sum(1 for d in dips if d<=-0.20)/len(dips)*100
    rets=[x[5] for x in g if x[5] is not None]
    lab=('%d–%d%%'%(int(lo*100 if lo>0 else 0),int(hi*100))) if hi<90 else ('%d%%+'%int(lo*100))
    print('   %-14s %6d %+7.1f%% %10.0f%% %8.0f%% %+8.1f%%'%(lab,len(g),med(dips),p10,p20,med(rets)))

# ---- C) time to revert to the 200MA by bucket ----
print('\nC) Median trading-days until price touches its 200MA again (of those that did within 1yr; % that reverted)')
for lo,hi in BUCK:
    g=[x for x in obs if lo<x[0]<=hi]
    if not g:continue
    d2=[x[7] for x in g if x[7] is not None]
    reverted=len(d2)/len(g)*100
    lab=('%d–%d%%'%(int(lo*100 if lo>0 else 0),int(hi*100))) if hi<90 else ('%d%%+'%int(lo*100))
    print('   %-14s reverted within 1yr: %3.0f%%   median days-to-touch: %s'%(lab,reverted, ('%d'%int(stt.median(d2))) if d2 else 'n/a'))

# ---- D) does RSI add anything on top of extension? ----
print('\nD) RSI(14) daily buckets (stock above 200MA): forward 63d dip & return')
for lo,hi in [(0,50),(50,60),(60,70),(70,80),(80,101)]:
    g=[x for x in obs if x[1] is not None and lo<=x[1]<hi]
    if not g:continue
    dips=[x[3] for x in g if x[3] is not None]
    rets=[x[5] for x in g if x[5] is not None]
    p10=sum(1 for d in dips if d<=-0.10)/len(dips)*100
    print('   RSI %3d-%-3d  n=%6d  medDip %+6.1f%%  P(>=10%%dip) %3.0f%%  medRet63 %+6.1f%%'%(lo,hi,len(g),med(dips),p10,med(rets)))

# ---- E) run-length: how long already extended vs forward dip ----
print('\nE) How long already above 200MA (run length) vs forward 63d dip')
for lo,hi in [(1,60),(60,180),(180,360),(360,720),(720,99999)]:
    g=[x for x in obs if lo<=x[2]<hi]
    if not g:continue
    dips=[x[3] for x in g if x[3] is not None]
    rets=[x[5] for x in g if x[5] is not None]
    lab='%d-%dd'%(lo,hi) if hi<99999 else '%d+d'%lo
    print('   above %-9s n=%6d  medDip %+6.1f%%  medRet63 %+6.1f%%'%(lab,len(g),med(dips),med(rets)))
