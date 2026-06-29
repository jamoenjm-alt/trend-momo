#!/usr/bin/env python3
"""
PROVE - honest multi-strategy research engine.
Tests canonical strategies on a broad universe vs SPY, with split-sample (H1/H2)
validation. A strategy is only "proven" if it beats SPY risk-adjusted in BOTH halves.
Run on your machine:  python prove.py
Writes prove-results.json. No site math here - these are standalone, well-known signals.
"""
import os, sys, json, math, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
YEARS = 11
BENCH = "SPY"
SAFE  = "AGG"   # bond ETF used as the 'cash' parking spot in risk-off

# Broad, sector-diversified large/mid-cap universe (includes laggards, not just winners).
UNIVERSE = [
 "AAPL","MSFT","NVDA","AMZN","GOOGL","META","AVGO","TSLA","ORCL","CRM","ADBE","AMD","INTC","CSCO","QCOM","TXN","IBM","NOW","INTU","AMAT","MU","ADI","LRCX","KLAC","SNPS","CDNS","PANW","ANET",
 "JPM","BAC","WFC","C","GS","MS","SCHW","AXP","BLK","SPGI","CB","PGR","MMC","PNC","USB","TFC",
 "UNH","JNJ","LLY","PFE","MRK","ABBV","TMO","ABT","DHR","BMY","AMGN","GILD","CVS","MDT","ISRG","VRTX","CI","HUM",
 "WMT","COST","PG","KO","PEP","MCD","NKE","SBUX","LOW","HD","TGT","DG","EL","CL","MDLZ","MO","PM","KHC",
 "XOM","CVX","COP","SLB","EOG","MPC","PSX","OXY","WMB","KMI",
 "BA","CAT","GE","HON","UNP","UPS","RTX","LMT","DE","MMM","EMR","ETN","CSX","NSC","FDX","GD","NOC",
 "DIS","NFLX","CMCSA","T","VZ","TMUS","CHTR",
 "LIN","APD","SHW","FCX","NEM","NUE","DOW",
 "NEE","DUK","SO","D","AEP","EXC",
 "PLD","AMT","EQIX","SPG","O","CCI",
 "SPY","QQQ","IWM","AGG"
]

def load_up():
    spec = importlib.util.spec_from_file_location("update_prices", os.path.join(HERE, "update-prices.py"))
    up = importlib.util.module_from_spec(spec); spec.loader.exec_module(up); return up

def fetch_all():
    up = load_up(); hist = {}
    syms = list(dict.fromkeys(UNIVERSE))
    for i, t in enumerate(syms):
        try:
            closes, h, l = up.fetch_yahoo(t, days=YEARS*365+30)
            if closes and len(closes) > 300:
                hist[t] = closes
                print(f"  [{i+1}/{len(syms)}] {t:6s} {len(closes)} bars")
            else:
                print(f"  [{i+1}/{len(syms)}] {t:6s} skip")
        except Exception as e:
            print(f"  {t} err {e}")
    json.dump(hist, open(os.path.join(HERE,"prove-history.json"),"w"))
    return hist

# ---------- metrics ----------
def cagr(eq, yrs): return (eq[-1]/eq[0])**(1/yrs)-1 if eq[-1]>0 else -1
def maxdd(eq):
    pk=eq[0]; mx=0
    for v in eq:
        pk=max(pk,v); mx=min(mx, v/pk-1)
    return mx
def sharpe(rets):
    if len(rets)<2: return 0
    m=sum(rets)/len(rets); var=sum((r-m)**2 for r in rets)/(len(rets)-1); sd=math.sqrt(var)
    return (m/sd)*math.sqrt(12) if sd>0 else 0   # monthly rets -> annualised

def sma(arr,n): return sum(arr[-n:])/n if len(arr)>=n else None

# ---------- backtester ----------
REBAL=21; LOOK=252; SKIP=21; TOPN=10

def backtest(hist, strat, idx_lo, idx_hi):
    """strat in {'csmom','dualmom','trendmom','ewhold'}; returns (equity list, monthly rets)."""
    uni=[t for t in UNIVERSE if t not in (BENCH,SAFE,"QQQ","IWM") and hist.get(t) and len(hist[t])>=idx_hi]
    spy=hist[BENCH]; agg=hist.get(SAFE)
    eq=[1.0]; rets=[]
    for t in range(idx_lo, idx_hi-REBAL, REBAL):
        # index trend (time-series filter)
        spyTrend = spy[t] > (sma(spy[:t+1],200) or 1e18)
        # cross-sectional momentum scores (12-1)
        scored=[]
        for tk in uni:
            c=hist[tk]
            if t-LOOK<0: continue
            mom = c[t-SKIP]/c[t-LOOK]-1
            scored.append((mom,tk))
        scored.sort(reverse=True)
        picks=[tk for _,tk in scored[:TOPN]]
        if strat=='ewhold': picks=uni  # equal-weight hold whole universe
        elif strat=='dualmom': picks=[tk for m,tk in scored[:TOPN] if m>0]  # absolute filter
        elif strat=='trendmom': picks = picks if spyTrend else []           # index-trend gate
        # period return
        if picks:
            r=sum(hist[tk][t+REBAL]/hist[tk][t]-1 for tk in picks)/len(picks)
        else:
            r= (agg[t+REBAL]/agg[t]-1) if agg else 0.0   # park in bonds
        eq.append(eq[-1]*(1+r)); rets.append(r)
    return eq, rets

def spy_bh(hist, lo, hi):
    spy=hist[BENCH]; eq=[1.0]; rets=[]
    for t in range(lo, hi-REBAL, REBAL):
        r=spy[t+REBAL]/spy[t]-1; eq.append(eq[-1]*(1+r)); rets.append(r)
    return eq, rets

def stats(eq, rets, yrs, label):
    return {"strategy":label,"CAGR":round(cagr(eq,yrs)*100,1),"total":round((eq[-1]-1)*100,0),
            "maxDD":round(maxdd(eq)*100,1),"sharpe":round(sharpe(rets),2)}

def main():
    print(f"PROVE: fetching ~{YEARS}y for {len(set(UNIVERSE))} symbols ...")
    hist=fetch_all()
    MINBARS=2300  # ~9y; drop short-history names so they don't truncate everyone
    keep={t:c for t,c in hist.items() if len(c)>=MINBARS or t in (BENCH,SAFE)}
    dropped=[t for t in hist if t not in keep]
    if dropped: print("  dropped (too short):", ", ".join(dropped))
    hist=keep
    L=min(len(hist[t]) for t in hist)
    for t in list(hist): hist[t]=hist[t][-L:]
    n=L; half=n//2; yrsFull=n/252; yrsH=half/252
    segs=[("FULL",LOOK+SKIP,n,yrsFull),("H1",LOOK+SKIP,half,(half-LOOK-SKIP)/252),("H2",half,n,(n-half)/252)]
    out={}
    for seg,lo,hi,yrs in segs:
        rows=[]
        b_eq,b_r=spy_bh(hist,lo,hi); rows.append(stats(b_eq,b_r,yrs,"SPY buy&hold"))
        for s in ['ewhold','csmom','dualmom','trendmom']:
            eq,r=backtest(hist,s,lo,hi); rows.append(stats(eq,r,yrs,s))
        out[seg]=rows
        print(f"\n=== {seg} ({yrs:.1f}y) ===")
        print(f"{'strategy':16s} {'CAGR':>6} {'total':>7} {'maxDD':>7} {'Sharpe':>7}")
        for x in rows: print(f"{x['strategy']:16s} {x['CAGR']:>5}% {x['total']:>6}% {x['maxDD']:>6}% {x['sharpe']:>7}")
    json.dump(out, open(os.path.join(HERE,"prove-results.json"),"w"), indent=1)
    print("\nPROVEN = beats SPY on CAGR *and* Sharpe in BOTH H1 and H2. Paste this output back.")

if __name__=="__main__": main()
