#!/usr/bin/env python3
"""
PROVE v3 - can a trend-filtered BTC sleeve raise return while controlling drawdown?
Date-aligned (BTC trades weekends; we map it onto the stock calendar).
Tests asset-allocation strategies (no single-stock survivorship issue) vs SPY.
Run:  python prove3.py
"""
import os, json, math, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
HERE=os.path.dirname(os.path.abspath(__file__))
YEARS=11; REBAL=21; LOOK=252; SKIP=21; COST=0.0010
ETFS=["XLK","XLF","XLE","XLV","XLY","XLP","XLI","XLB","XLU","TLT","GLD","EEM","EFA","IWM","QQQ","VNQ","HYG"]
NEED=["SPY","AGG","BTC-USD"]+ETFS

def fetch_dated(sym, days=YEARS*365+40, retries=3):
    end=int(datetime.now(timezone.utc).timestamp()); start=int((datetime.now(timezone.utc)-timedelta(days=days)).timestamp())
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?interval=1d&period1={start}&period2={end}"
    hdr={"User-Agent":"Mozilla/5.0"}
    for a in range(retries):
        if a: time.sleep(2**a)
        try:
            raw=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=hdr),timeout=25).read().decode())
            r=raw["chart"]["result"][0]; ts=r["timestamp"]; cl=r["indicators"]["quote"][0]["close"]
            out={}
            for t,c in zip(ts,cl):
                if c is None: continue
                d=datetime.fromtimestamp(t,timezone.utc).strftime("%Y-%m-%d"); out[d]=round(c,4)
            return out
        except Exception as e:
            if a==retries-1: print(f"  {sym} ERR {e}")
    return {}

def get_panel():
    cache=os.path.join(HERE,"prove3-panel.json")
    if os.path.exists(cache):
        p=json.load(open(cache))
        if all(s in p for s in NEED): print("using cached prove3-panel.json"); return p
    print(f"fetching {len(NEED)} symbols (date-aware) ...")
    p={}
    for s in NEED:
        p[s]=fetch_dated(s); print(f"  {s:8s} {len(p[s])} days"); time.sleep(0.3)
    json.dump(p,open(cache,"w")); return p

def align(panel):
    # calendar = SPY trading days that ALL symbols have a price for
    days=set(panel["SPY"])
    for s in NEED: days &= set(panel[s])
    cal=sorted(days)
    return cal, {s:[panel[s][d] for d in cal] for s in NEED}

def cagr(eq,y): return eq[-1]**(1/y)-1 if eq[-1]>0 else -1
def mdd(eq):
    pk=eq[0]; m=0
    for v in eq: pk=max(pk,v); m=min(m,v/pk-1)
    return m
def sharpe(r):
    if len(r)<2: return 0
    mu=sum(r)/len(r); sd=math.sqrt(sum((x-mu)**2 for x in r)/(len(r)-1)); return (mu/sd)*math.sqrt(12) if sd else 0
def sma(a,n): return sum(a[-n:])/n if len(a)>=n else None
def dailyMDD(series): return mdd(series)   # true daily drawdown of a raw price series

def seg_run(S, lo, hi):
    """returns dict of strategy -> (eqcurve, monthly rets)"""
    spy=S["SPY"]; agg=S["AGG"]; btc=S["BTC-USD"]
    res={}
    def bh(sym):
        eq=[1.0]; r=[]
        for t in range(lo,hi-REBAL,REBAL): x=S[sym][t+REBAL]/S[sym][t]-1; eq.append(eq[-1]*(1+x)); r.append(x)
        return eq,r
    res["SPY b&h"]=bh("SPY"); res["BTC b&h"]=bh("BTC-USD")
    # 60/40
    eq=[1.0]; r=[]
    for t in range(lo,hi-REBAL,REBAL):
        x=0.6*(spy[t+REBAL]/spy[t]-1)+0.4*(agg[t+REBAL]/agg[t]-1); eq.append(eq[-1]*(1+x)); r.append(x)
    res["60/40 SPY/AGG"]=(eq,r)
    # ETF dual momentum (+/- BTC)
    def etfmom(univ,topn):
        eq=[1.0]; r=[]; prev=set()
        for t in range(lo,hi-REBAL,REBAL):
            sc=[]
            for tk in univ:
                if t-LOOK<0: continue
                sc.append((S[tk][t-SKIP]/S[tk][t-LOOK]-1,tk))
            sc.sort(reverse=True); picks=[tk for m,tk in sc[:topn] if m>0]
            x=(sum(S[tk][t+REBAL]/S[tk][t]-1 for tk in picks)/len(picks)) if picks else (agg[t+REBAL]/agg[t]-1)
            nw=set(picks); x-=COST*(len(nw^prev)/max(len(nw|prev),1)); prev=nw
            eq.append(eq[-1]*(1+x)); r.append(x)
        return eq,r
    res["ETF mom (no BTC)"]=etfmom(ETFS,4)
    res["ETF mom + BTC"]=etfmom(ETFS+["BTC-USD"],4)
    # core + trend-filtered BTC satellite, several weights
    for w in (0.05,0.10,0.20):
        eq=[1.0]; r=[]
        for t in range(lo,hi-REBAL,REBAL):
            trend = btc[t] > (sma(btc[:t+1],200) or 1e18)
            sat = (btc[t+REBAL]/btc[t]-1) if trend else (agg[t+REBAL]/agg[t]-1)
            x=(1-w)*(spy[t+REBAL]/spy[t]-1)+w*sat
            eq.append(eq[-1]*(1+x)); r.append(x)
        res[f"SPY+{int(w*100)}% BTC(trend)"]=(eq,r)
    return res

def main():
    panel=get_panel(); cal,S=align(panel)
    n=len(cal); print(f"\naligned trading days: {n} ({n/252:.1f}y)  {cal[0]} -> {cal[-1]}")
    print(f"BTC true daily max drawdown over window: {dailyMDD(S['BTC-USD'])*100:.0f}%  (this is the real risk monthly numbers hide)")
    half=n//2
    for seg,lo,hi in [("FULL",LOOK+SKIP,n),("H1",LOOK+SKIP,half),("H2",half,n)]:
        y=(hi-lo)/252; res=seg_run(S,lo,hi)
        print(f"\n=== {seg} ({y:.1f}y) ===")
        print(f"{'strategy':22s} {'CAGR':>6} {'total':>8} {'maxDD*':>7} {'Sharpe':>7}")
        for k,(eq,r) in res.items():
            print(f"{k:22s} {cagr(eq,y)*100:>5.1f}% {(eq[-1]-1)*100:>7.0f}% {mdd(eq)*100:>6.1f}% {sharpe(r):>7.2f}")
    print("\n*maxDD is monthly-resolution; true intra-month drawdowns (esp. BTC) are deeper.")
    print("PROVEN = beats SPY on CAGR and Sharpe in BOTH H1 and H2, with maxDD no worse than SPY.")

if __name__=="__main__": main()
