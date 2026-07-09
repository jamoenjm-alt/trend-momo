#!/usr/bin/env python3
"""
DEEP BACKTEST — Waterleak / Waterflow / Waterfall / Water Rapids from 2002.
Point-in-time top-10 US mega-caps (membership refreshed yearly, incl. the financials
that blew up in 2008 — Citi, AIG — so the crash is tested honestly). Daily 200-day
trend filter. Costs 5bps/side. Run on your machine (needs Yahoo):  python deep-backtest.py
BTC only exists from ~2014, so Water Rapids is reported from BTC inception onward.
NOTE: 2002-2009 top-10 lists are best-effort from public record; giants rarely vanish but
Citi/AIG were reverse-split & bailed out (Yahoo adjusted-close reflects the shareholder loss).
"""
import urllib.request, urllib.parse, json, math, time
from datetime import datetime, timezone

TOP10 = {
 2002:["GE","MSFT","XOM","WMT","C","PFE","JNJ","IBM","AIG","INTC"],
 2003:["GE","MSFT","XOM","WMT","PFE","C","JNJ","AIG","IBM","PG"],
 2004:["GE","XOM","MSFT","WMT","C","PFE","BAC","JNJ","AIG","IBM"],
 2005:["GE","XOM","MSFT","C","WMT","BAC","PFE","JNJ","AIG","PG"],
 2006:["XOM","GE","MSFT","C","BAC","WMT","PG","JNJ","AIG","PFE"],
 2007:["XOM","GE","MSFT","C","AIG","BAC","WMT","PG","JNJ","CVX"],
 2008:["XOM","GE","MSFT","WMT","PG","JNJ","CVX","T","JPM","BAC"],
 2009:["XOM","WMT","MSFT","PG","JNJ","GE","JPM","CVX","IBM","T"],
 2010:["XOM","MSFT","AAPL","WMT","GOOGL","JNJ","PG","IBM","GE","CVX"],
 2011:["XOM","AAPL","MSFT","IBM","CVX","WMT","GE","GOOGL","JNJ","PG"],
 2012:["AAPL","XOM","MSFT","IBM","WMT","GE","CVX","GOOGL","JNJ","PG"],
 2013:["AAPL","XOM","GOOGL","MSFT","GE","JNJ","WMT","CVX","PG","WFC"],
 2014:["AAPL","XOM","MSFT","GOOGL","JNJ","GE","WFC","WMT","PG","CVX"],
 2015:["AAPL","GOOGL","MSFT","XOM","JNJ","GE","WFC","AMZN","META","PG"],
 2016:["AAPL","GOOGL","MSFT","AMZN","META","XOM","JNJ","JPM","GE","WFC"],
 2017:["AAPL","GOOGL","MSFT","AMZN","META","BRK-B","JNJ","XOM","JPM","WFC"],
 2018:["AAPL","MSFT","AMZN","GOOGL","META","BRK-B","JPM","JNJ","XOM","V"],
 2019:["MSFT","AAPL","AMZN","GOOGL","META","BRK-B","JPM","JNJ","V","XOM"],
 2020:["AAPL","MSFT","AMZN","GOOGL","META","BRK-B","V","JNJ","WMT","JPM"],
 2021:["AAPL","MSFT","AMZN","GOOGL","META","TSLA","BRK-B","V","JPM","JNJ"],
 2022:["AAPL","MSFT","GOOGL","AMZN","TSLA","META","BRK-B","NVDA","JNJ","V"],
 2023:["AAPL","MSFT","GOOGL","AMZN","BRK-B","NVDA","TSLA","XOM","UNH","JNJ"],
 2024:["AAPL","MSFT","GOOGL","AMZN","NVDA","META","BRK-B","LLY","TSLA","V"],
 2025:["AAPL","MSFT","NVDA","GOOGL","AMZN","META","BRK-B","TSLA","AVGO","LLY"],
 2026:["AAPL","MSFT","NVDA","GOOGL","AMZN","META","BRK-B","TSLA","AVGO","LLY"],
}
YMAP={"BRK-B":"BRK-B","BTC":"BTC-USD"}
EXTRA=["SPY","AGG","BTC-USD"]
NAMES=sorted({t for lst in TOP10.values() for t in lst} | set(EXTRA))

def fetch(sym):
    end=int(datetime.now(timezone.utc).timestamp()); start=int(datetime(2001,1,1,tzinfo=timezone.utc).timestamp())
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?interval=1d&period1={start}&period2={end}"
    for a in range(3):
        if a: time.sleep(2**a)
        try:
            raw=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode())
            r=raw["chart"]["result"][0]; ts=r["timestamp"]; cl=r["indicators"]["quote"][0]["close"]
            adj=r.get("indicators",{}).get("adjclose",[{}])[0].get("adjclose",cl)
            out={}
            for t,c in zip(ts,adj if adj else cl):
                if c is not None: out[datetime.fromtimestamp(t,timezone.utc).strftime("%Y-%m-%d")]=c
            return out
        except Exception as e:
            if a==2: print(f"  {sym} ERR {e}")
    return {}

def main():
    cache="deep-panel.json"
    import os
    if os.path.exists(cache):
        P=json.load(open(cache)); print("using cached deep-panel.json")
    else:
        print(f"fetching {len(NAMES)} symbols back to 2002 (a few minutes)...")
        P={}
        for s in NAMES:
            P[s]=fetch(s); print(f"  {s:7s} {len(P[s])} days"); time.sleep(0.25)
        json.dump(P,open(cache,"w"))
    SPY=P["SPY"]; AGG=P.get("AGG",{}); BTC=P.get("BTC-USD",{})
    CAL=sorted(SPY)
    def sma(series,keys):
        out={}; run=0
        for i,d in enumerate(keys):
            v=series.get(d)
            if v is None: out[d]=out.get(keys[i-1]) if i else None; continue
            run+=v
            if i>=200: run-= series.get(keys[i-200],0)
            out[d]=run/200 if i>=199 else None
        return out
    spySMA=sma(SPY,CAL); btcSMA=sma(BTC,sorted(BTC)) if BTC else {}
    def bret(a,b):
        yr=int(b[:4]); mem=[t for t in TOP10.get(yr,TOP10[2026]) if t in P and P[t].get(a) and P[t].get(b)]
        return (sum(P[t][b]/P[t][a]-1 for t in mem)/len(mem)) if mem else 0.0
    def run(mode, lo):
        eq=[1.0]; dts=[CAL[lo]]; state=1; bstate=1; C=0.0005
        for i in range(lo+1,len(CAL)):
            a,b=CAL[i-1],CAL[i]
            er=bret(a,b); sr=(SPY[b]/SPY[a]-1)
            spyOn = spySMA.get(a) and SPY[a]>spySMA[a]
            btr = (BTC[b]/BTC[a]-1) if (b in BTC and a in BTC) else 0.0
            btcOn = btcSMA.get(a) and a in BTC and BTC[a]>btcSMA[a]
            if mode=='leak': r=sr
            elif mode=='flow':
                w=1 if spyOn else 0; c=C if w!=state else 0; state=w; r=(er if w else 0)-c
            elif mode=='fall': r=er
            elif mode=='rapids':
                w=1 if spyOn else 0; bw=1 if btcOn else 0
                c=(C if w!=state else 0)+(C if bw!=bstate else 0); state=w; bstate=bw
                r=0.85*(er if w else 0)+0.15*(btr if bw else 0)-c
            eq.append(eq[-1]*(1+r)); dts.append(b)
        return dts,eq
    def stats(dts,eq):
        y=(len(eq))/252; c=eq[-1]**(1/y)-1; pk=eq[0]; dd=0; ddyear=None
        for i,v in enumerate(eq):
            pk=max(pk,v)
            if v/pk-1<dd: dd=v/pk-1
        # 2008 drawdown specifically
        idx=[i for i,d in enumerate(dts) if '2007-06'<=d<='2009-06']
        dd08=0
        if idx:
            pk=eq[idx[0]]
            for i in idx: pk=max(pk,eq[i]); dd08=min(dd08,eq[i]/pk-1)
        r=[eq[i]/eq[i-1]-1 for i in range(1,len(eq))]; mu=sum(r)/len(r); sd=math.sqrt(sum((x-mu)**2 for x in r)/(len(r)-1))
        return c*100,dd*100,dd08*100,(mu/sd)*math.sqrt(252),eq[-1]
    lo=201
    print(f"\nDEEP BACKTEST  {CAL[lo]} -> {CAL[-1]}  ({(len(CAL)-lo)/252:.1f}y)")
    print(f"{'model':26s}{'CAGR':>7}{'maxDD':>8}{'2008DD':>8}{'Sharpe':>8}{'x':>8}")
    for name,mode in [('Waterleak (SPY)','leak'),('Waterflow (filtered)','flow'),('Waterfall (always-in)','fall')]:
        d,e=run(mode,lo); c,dd,dd08,sh,x=stats(d,e); print(f"{name:26s}{c:6.1f}%{dd:7.1f}%{dd08:7.1f}%{sh:8.2f}{x:8.1f}")
    if BTC:
        blo=CAL.index(min(d for d in CAL if d in BTC and CAL.index(d)>250)) if any(d in BTC for d in CAL) else None
        # start rapids at first day BTC has >200 days of history
        bdays=sorted(BTC); 
        if len(bdays)>210:
            startd=bdays[210]
            rlo=next((i for i,d in enumerate(CAL) if d>=startd),lo)
            d,e=run('rapids',rlo); c,dd,dd08,sh,x=stats(d,e)
            print(f"{'Water Rapids (BTC '+CAL[rlo][:4]+'+)':26s}{c:6.1f}%{dd:7.1f}%{'  n/a':>7}{sh:8.2f}{x:8.1f}")
    print("\nWatch the 2008DD column: if Waterflow's 2008 drawdown is much shallower than Waterfall's,")
    print("the trend filter did its job through a real crash. That is the whole test.")

if __name__=="__main__": main()
