#!/usr/bin/env python3
# Calibrate the stretch gauge: real extension distribution (price/200dMA-1) incl.
# deep tail, SEPARATELY for megacap equities and crypto(BTC), + forward-63d dip
# base rates for high buckets. Output baked breakpoints for the JS gauge.
import json, statistics as stt
P=json.load(open('backtests/deep-panel.json'))
dates=sorted(P['SPY'].keys())
def col(t): return [P[t].get(d) for d in dates]
def sma(cl,i,w):
    if i+1<w:return None
    s=0.0
    for k in range(i-w+1,i+1):
        v=cl[k]
        if v is None:return None
        s+=v
    return s/w
def worst_dip(cl,i,H=63):
    e=cl[i]
    if e is None or e<=0:return None
    lo=0.0
    for k in range(i+1,min(i+H+1,len(cl))):
        v=cl[k]
        if v is None:continue
        r=v/e-1
        if r<lo:lo=r
    return lo

EQ=[t for t in sorted(P) if t not in {'SPY','AGG','BTC-USD'}]
def gather(tickers):
    exts=[];dip=[]
    for t in tickers:
        cl=col(t)
        for i in range(len(cl)):
            m=sma(cl,i,200)
            if m is None or cl[i] is None or cl[i]<=m: continue
            e=cl[i]/m-1
            exts.append(e)
            if i+63<len(cl):
                d=worst_dip(cl,i,63)
                if d is not None: dip.append((e,d))
    return exts,dip
def pctls(a,ps):
    a=sorted(a); n=len(a)
    return {p: a[min(n-1,int(p/100*(n-1)))] for p in ps}
PS=[5,25,50,75,90,95,97,99,99.9]
for name,tickers in [('EQUITY megacaps',EQ),('CRYPTO (BTC)',['BTC-USD'])]:
    exts,dip=gather(tickers)
    pc=pctls(exts,PS)
    print('\n=== %s === (n=%d days above 200MA, max ext %+.0f%%)'%(name,len(exts),max(exts)*100))
    print('  percentiles of extension above 200d MA:')
    for p in PS: print('    p%-5s %+6.0f%%'%(p,pc[p]*100))
    # dip base rates by bucket
    B=[(-1,.20),(.20,.35),(.35,.50),(.50,.80),(.80,1.20),(1.20,99)]
    print('  forward 63d dip by extension bucket:')
    for lo,hi in B:
        g=[d for e,d in dip if lo<e<=hi]
        if len(g)<20:
            lab=('%d-%d%%'%(int(max(lo,0)*100),int(hi*100))) if hi<90 else ('%d%%+'%int(lo*100))
            print('    %-10s n=%-5d (too few)'%(lab,len(g)));continue
        p10=sum(1 for d in g if d<=-0.10)/len(g)*100
        p20=sum(1 for d in g if d<=-0.20)/len(g)*100
        lab=('%d-%d%%'%(int(max(lo,0)*100),int(hi*100))) if hi<90 else ('%d%%+'%int(lo*100))
        print('    %-10s n=%-5d medDip %+6.1f%%  P(>=10%%) %3.0f%%  P(>=20%%) %3.0f%%'%(lab,len(g),stt.median(g)*100,p10,p20))
    # emit JS breakpoint array (percentile -> ext) for the gauge
    arr=[round(pc[p],3) for p in [5,25,50,75,90,95,99,99.9]]
    print('  JS breakpoints [p5,p25,p50,p75,p90,p95,p99,p99.9] =',arr)
