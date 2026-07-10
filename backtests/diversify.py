#!/usr/bin/env python3
"""
DIVERSIFY — blend Waterflow with gold + long bonds (+ commodities) and find the
best risk-adjusted mix, 2004-2026 incl. 2008. Run:  python diversify.py
Fetches GLD (gold), TLT (long treasuries), DBC (commodities); reuses deep-panel.json.
"""
import urllib.request, urllib.parse, json, math, time, os
from datetime import datetime, timezone
EXTRA=["GLD","TLT","DBC"]
def fetch(sym):
    end=int(datetime.now(timezone.utc).timestamp()); start=int(datetime(2003,1,1,tzinfo=timezone.utc).timestamp())
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?interval=1d&period1={start}&period2={end}"
    for a in range(3):
        if a: time.sleep(2**a)
        try:
            raw=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode())
            r=raw["chart"]["result"][0];ts=r["timestamp"];adj=r["indicators"].get("adjclose",[{}])[0].get("adjclose") or r["indicators"]["quote"][0]["close"]
            return {datetime.fromtimestamp(t,timezone.utc).strftime("%Y-%m-%d"):c for t,c in zip(ts,adj) if c is not None}
        except Exception as e:
            if a==2: print(f"  {sym} ERR {e}")
    return {}
TOP10={2002:["GE","MSFT","XOM","WMT","C","PFE","JNJ","IBM","AIG","INTC"],2003:["GE","MSFT","XOM","WMT","PFE","C","JNJ","AIG","IBM","PG"],2004:["GE","XOM","MSFT","WMT","C","PFE","BAC","JNJ","AIG","IBM"],2005:["GE","XOM","MSFT","C","WMT","BAC","PFE","JNJ","AIG","PG"],2006:["XOM","GE","MSFT","C","BAC","WMT","PG","JNJ","AIG","PFE"],2007:["XOM","GE","MSFT","C","AIG","BAC","WMT","PG","JNJ","CVX"],2008:["XOM","GE","MSFT","WMT","PG","JNJ","CVX","T","JPM","BAC"],2009:["XOM","WMT","MSFT","PG","JNJ","GE","JPM","CVX","IBM","T"],2010:["XOM","MSFT","AAPL","WMT","GOOGL","JNJ","PG","IBM","GE","CVX"],2011:["XOM","AAPL","MSFT","IBM","CVX","WMT","GE","GOOGL","JNJ","PG"],2012:["AAPL","XOM","MSFT","IBM","WMT","GE","CVX","GOOGL","JNJ","PG"],2013:["AAPL","XOM","GOOGL","MSFT","GE","JNJ","WMT","CVX","PG","WFC"],2014:["AAPL","XOM","MSFT","GOOGL","JNJ","GE","WFC","WMT","PG","CVX"],2015:["AAPL","GOOGL","MSFT","XOM","JNJ","GE","WFC","AMZN","META","PG"],2016:["AAPL","GOOGL","MSFT","AMZN","META","XOM","JNJ","JPM","GE","WFC"],2017:["AAPL","GOOGL","MSFT","AMZN","META","BRK-B","JNJ","XOM","JPM","WFC"],2018:["AAPL","MSFT","AMZN","GOOGL","META","BRK-B","JPM","JNJ","XOM","V"],2019:["MSFT","AAPL","AMZN","GOOGL","META","BRK-B","JPM","JNJ","V","XOM"],2020:["AAPL","MSFT","AMZN","GOOGL","META","BRK-B","V","JNJ","WMT","JPM"],2021:["AAPL","MSFT","AMZN","GOOGL","META","TSLA","BRK-B","V","JPM","JNJ"],2022:["AAPL","MSFT","GOOGL","AMZN","TSLA","META","BRK-B","NVDA","JNJ","V"],2023:["AAPL","MSFT","GOOGL","AMZN","BRK-B","NVDA","TSLA","XOM","UNH","JNJ"],2024:["AAPL","MSFT","GOOGL","AMZN","NVDA","META","BRK-B","LLY","TSLA","V"],2025:["AAPL","MSFT","NVDA","GOOGL","AMZN","META","BRK-B","TSLA","AVGO","LLY"],2026:["AAPL","MSFT","NVDA","GOOGL","AMZN","META","BRK-B","TSLA","AVGO","LLY"]}
def main():
    if not os.path.exists("deep-panel.json"):
        print("Run deep-backtest.py first (need deep-panel.json)."); return
    P=json.load(open("deep-panel.json"))
    print("fetching GLD, TLT, DBC ..."); 
    for s in EXTRA: P[s]=fetch(s); print(f"  {s} {len(P[s])}")
    SPY=P["SPY"];GLD=P["GLD"];TLT=P["TLT"];DBC=P.get("DBC",{})
    CAL=sorted(set(SPY)&set(GLD)&set(TLT))
    sv=[SPY[d] for d in CAL];sma=[None]*len(CAL);run=0
    for i in range(len(CAL)):
        run+=sv[i]
        if i>=200:run-=sv[i-200]
        if i>=199:sma[i]=sv[i]>run/200
    def bret(a,b):
        yr=int(b[:4]);mem=[t for t in TOP10.get(yr,TOP10[2026]) if t in P and P[t].get(a) and P[t].get(b)]
        return sum(P[t][b]/P[t][a]-1 for t in mem)/len(mem) if mem else 0.0
    def blend(wf,gold,bond,com=0.0):
        eq=[1.0];dts=[CAL[201]];st=None;C=0.0005
        for i in range(202,len(CAL)):
            a,b=CAL[i-1],CAL[i];er=bret(a,b);up=sma[i-1]
            c=C if(st is not None and (('L' if up else '0')!=st))else 0;st='L' if up else '0'
            wfr=(er if up else 0)-c
            gr=GLD[b]/GLD[a]-1;br=TLT[b]/TLT[a]-1;dr=(DBC[b]/DBC[a]-1) if(b in DBC and a in DBC) else 0
            eq.append(eq[-1]*(1+wf*wfr+gold*gr+bond*br+com*dr));dts.append(b)
        return dts,eq
    def stt(dts,eq):
        y=len(eq)/252;c=eq[-1]**(1/y)-1;pk=eq[0];dd=0
        for v in eq:pk=max(pk,v);dd=min(dd,v/pk-1)
        idx=[i for i,d in enumerate(dts) if '2007-06'<=d<='2009-06'];dd08=0
        if idx:
            pk=eq[idx[0]]
            for i in idx:pk=max(pk,eq[i]);dd08=min(dd08,eq[i]/pk-1)
        yr={}
        for i in range(1,len(dts)):yr.setdefault(dts[i][:4],[]).append(eq[i]/eq[i-1]-1)
        wy=min(math.prod([1+x for x in v])-1 for v in yr.values())
        r=[eq[i]/eq[i-1]-1 for i in range(1,len(eq))];mu=sum(r)/len(r);sd=math.sqrt(sum((x-mu)**2 for x in r)/(len(r)-1))
        return c*100,dd*100,dd08*100,wy*100,(mu/sd)*math.sqrt(252)
    print(f"\nWindow {CAL[201]} -> {CAL[-1]}  (gold available)")
    print(f"{'blend  WF/Gold/Bond/Comm':30s}{'CAGR':>7}{'maxDD':>8}{'2008':>7}{'worstYr':>9}{'Sharpe':>7}")
    mixes=[("100/0/0/0",1,0,0,0),("80/10/10/0",.8,.1,.1,0),("60/20/20/0",.6,.2,.2,0),("60/15/15/10",.6,.15,.15,.10),("50/25/25/0",.5,.25,.25,0),("40/30/30/0",.4,.3,.3,0),("50/20/20/10",.5,.2,.2,.10)]
    for name,w,g,bd,co in mixes:
        d,e=blend(w,g,bd,co);s=stt(d,e);print(f"{name:30s}{s[0]:7.1f}{s[1]:8.1f}{s[2]:7.1f}{s[3]:9.1f}{s[4]:7.2f}")
    print("\nBest Sharpe = best risk-adjusted. Growth falls as you add gold/bonds — pick your rung.")
if __name__=="__main__": main()
