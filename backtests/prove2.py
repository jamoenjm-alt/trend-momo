#!/usr/bin/env python3
"""
PROVE v2 - attack the survivorship/concentration/cost flaws in the 30% momentum result.
Adds: transaction costs, an ex-top-winners stock test, and a BIAS-FREE sector/asset ETF
universe (the genuinely tradeable test). Reuses prove-history.json; only fetches new ETFs.
Run:  python prove2.py
"""
import os, json, math, importlib.util
HERE=os.path.dirname(os.path.abspath(__file__))
YEARS=11; BENCH="SPY"; SAFE="AGG"
REBAL=21; LOOK=252; SKIP=21; COST=0.0010   # 10 bps per side, charged on turnover

STOCKS=["AAPL","MSFT","NVDA","AMZN","GOOGL","META","AVGO","TSLA","ORCL","CRM","ADBE","AMD","INTC","CSCO","QCOM","TXN","IBM","NOW","INTU","AMAT","MU","ADI","LRCX","KLAC","SNPS","CDNS","PANW","ANET","JPM","BAC","WFC","C","GS","MS","SCHW","AXP","BLK","SPGI","CB","PGR","PNC","USB","TFC","UNH","JNJ","LLY","PFE","MRK","ABBV","TMO","ABT","DHR","BMY","AMGN","GILD","CVS","MDT","ISRG","VRTX","CI","HUM","WMT","COST","PG","KO","PEP","MCD","NKE","SBUX","LOW","HD","TGT","DG","EL","CL","MDLZ","MO","PM","KHC","XOM","CVX","COP","SLB","EOG","MPC","PSX","OXY","WMB","KMI","BA","CAT","GE","HON","UNP","UPS","RTX","LMT","DE","MMM","EMR","ETN","CSX","NSC","FDX","GD","NOC","DIS","NFLX","CMCSA","T","VZ","TMUS","CHTR","LIN","APD","SHW","FCX","NEM","NUE","NEE","DUK","SO","D","AEP","EXC","PLD","AMT","EQIX","SPG","O","CCI"]
ETFS=["XLK","XLF","XLE","XLV","XLY","XLP","XLI","XLB","XLU","XLRE","XLC","TLT","GLD","EEM","EFA","IWM","QQQ","VNQ","DBC","HYG"]
EXTRA=[BENCH,SAFE]

def load_up():
    s=importlib.util.spec_from_file_location("update_prices",os.path.join(HERE,"update-prices.py"))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def fetch():
    path=os.path.join(HERE,"prove-history.json")
    hist=json.load(open(path)) if os.path.exists(path) else {}
    up=load_up(); need=[t for t in dict.fromkeys(STOCKS+ETFS+EXTRA) if t not in hist]
    print(f"cached {len(hist)}, fetching {len(need)} new ...")
    for t in need:
        try:
            c,h,l=up.fetch_yahoo(t,days=YEARS*365+30)
            if c and len(c)>300: hist[t]=c; print(f"  {t} {len(c)}")
            else: print(f"  {t} skip")
        except Exception as e: print(f"  {t} err {e}")
    json.dump(hist,open(path,"w"))
    return hist

def cagr(eq,y): return (eq[-1])**(1/y)-1 if eq[-1]>0 else -1
def maxdd(eq):
    pk=eq[0]; mx=0
    for v in eq: pk=max(pk,v); mx=min(mx,v/pk-1)
    return mx
def sharpe(r):
    if len(r)<2: return 0
    m=sum(r)/len(r); sd=math.sqrt(sum((x-m)**2 for x in r)/(len(r)-1))
    return (m/sd)*math.sqrt(12) if sd>0 else 0
def sma(a,n): return sum(a[-n:])/n if len(a)>=n else None

def momrun(hist, uni, topn, lo, hi, cost=COST):
    uni=[t for t in uni if hist.get(t) and len(hist[t])>=hi]
    eq=[1.0]; rets=[]; prev=set()
    for t in range(lo,hi-REBAL,REBAL):
        sc=[]
        for tk in uni:
            if t-LOOK<0: continue
            sc.append((hist[tk][t-SKIP]/hist[tk][t-LOOK]-1, tk))
        sc.sort(reverse=True)
        picks=[tk for m,tk in sc[:topn] if m>0]            # absolute filter (dual momentum)
        if picks:
            r=sum(hist[tk][t+REBAL]/hist[tk][t]-1 for tk in picks)/len(picks)
        else:
            r=(hist[SAFE][t+REBAL]/hist[SAFE][t]-1) if hist.get(SAFE) else 0.0
        nw=set(picks); turn=len(nw.symmetric_difference(prev))/max(len(nw|prev),1)
        r-=cost*turn; prev=nw
        eq.append(eq[-1]*(1+r)); rets.append(r)
    return eq,rets

def bh(hist,sym,lo,hi):
    c=hist[sym]; eq=[1.0]; rets=[]
    for t in range(lo,hi-REBAL,REBAL):
        x=c[t+REBAL]/c[t]-1; eq.append(eq[-1]*(1+x)); rets.append(x)
    return eq,rets

def row(eq,r,y,label): return f"{label:26s} {cagr(eq,y)*100:>5.1f}% {(eq[-1]-1)*100:>7.0f}% {maxdd(eq)*100:>6.1f}% {sharpe(r):>6.2f}"

def main():
    hist=fetch()
    keep={t:c for t,c in hist.items() if len(c)>=2300}
    L=min(len(c) for c in keep.values()); hist={t:c[-L:] for t,c in keep.items()}
    # top-5 all-time winners in stock universe (for ex-winners test)
    tot=sorted(((hist[t][-1]/hist[t][0],t) for t in STOCKS if t in hist),reverse=True)
    winners=set(t for _,t in tot[:5]); stocks_ex=[t for t in STOCKS if t not in winners]
    n=L; half=n//2
    segs=[("FULL",LOOK+SKIP,n),("H1",LOOK+SKIP,half),("H2",half,n)]
    print(f"\nwindow {n/252:.1f}y | top-5 winners excluded in ex-test: {sorted(winners)}")
    for seg,lo,hi in segs:
        y=(hi-lo)/252
        print(f"\n=== {seg} ({y:.1f}y) ===")
        print(f"{'strategy':26s} {'CAGR':>6} {'total':>8} {'maxDD':>7} {'Sharpe':>7}")
        be,br=bh(hist,BENCH,lo,hi); print(row(be,br,y,"SPY buy&hold"))
        e,r=momrun(hist,STOCKS,10,lo,hi);       print(row(e,r,y,"stocks mom (net cost)"))
        e,r=momrun(hist,stocks_ex,10,lo,hi);    print(row(e,r,y,"stocks mom EX-winners"))
        e,r=momrun(hist,ETFS,4,lo,hi);          print(row(e,r,y,"ETF mom (BIAS-FREE)"))
    print("\nWatch the ETF row across H1 and H2 - that's the only bias-free, tradeable test.")

if __name__=="__main__": main()
