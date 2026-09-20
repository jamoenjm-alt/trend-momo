#!/usr/bin/env python3
# ============================================================================
#  horizon-lab.py  (2026-09-20)
#  PRE-REGISTERED per-horizon indicator test for the Signal-page "Best buy by
#  hold length" panel. Rules fixed BEFORE looking at results:
#
#  - Universe: deep-panel equities (survivors; SPY/AGG/BTC excluded). Survivorship
#    bias acknowledged -> absolute numbers are OPTIMISTIC. We therefore judge each
#    indicator RELATIVE to the equal-weight "average name" null, which carries the
#    same bias, so the *selection* edge is what survives.
#  - For each horizon H (5,21,126,252,1260 trading days) and each candidate
#    indicator, at monthly rebalance dates pick the SINGLE top name (mirrors the
#    live card = one pick), hold H days, record forward return. Costs 15bps/side.
#  - Split rebalance dates into first half / second half by time.
#  - A candidate QUALIFIES for a horizon only if its mean forward return beats the
#    equal-weight null in BOTH halves. Among qualifiers, prefer the one that also
#    beats SPY in both halves, then highest full-period mean. If none qualify ->
#    that horizon has NO selection edge; the card is greyed and says so.
#  - No parameter is tuned after seeing results.
# ============================================================================
import json, statistics as st

P = json.load(open('backtests/deep-panel.json'))
EXCL = {'SPY','AGG','BTC-USD'}
TICKERS = [t for t in sorted(P) if t not in EXCL]

# ---- align all series onto SPY's trading calendar ----
dates = sorted(P['SPY'].keys())
def series(t):
    d = P[t]
    return [d.get(day) for day in dates]     # None where missing
SPY = series('SPY')
COL = {t: series(t) for t in TICKERS}

# ---------- board signal math (faithful port of computeSignals) ----------
MA_PAIRS = [(10,3,'canary'),(15,5,'canary'),(42,10,'st'),(50,15,'st'),(63,21,'st'),
            (84,21,'lt'),(126,42,'lt'),(168,42,'lt'),(200,50,'all'),(252,63,'all')]
def sma(cl, w, i):
    # mean of cl[i-w+1 .. i]
    if i+1 < w: return None
    s=0.0
    for k in range(i-w+1, i+1):
        v=cl[k]
        if v is None: return None
        s+=v
    return s/w
def signals(cl, i):
    price = cl[i]
    if price is None: return None
    def colavg(groups):
        vals=[]
        for slow,fast,g in MA_PAIRS:
            if g not in groups: continue
            sM=sma(cl,slow,i); fM=sma(cl,fast,i)
            if sM is not None: vals.append(1 if price>sM else -1)
            if fM is not None and sM is not None: vals.append(1 if fM>sM else -1)
        return sum(vals)/len(vals) if vals else None
    return {'canary':colavg({'canary'}),'st':colavg({'st'}),'lt':colavg({'lt'}),
            'all':colavg({'canary','st','lt','all'})}
def ret(cl, i, back):
    if i-back < 0: return None
    a=cl[i-back]; b=cl[i]
    if a is None or b is None or a<=0: return None
    return b/a-1.0

# ---------- candidate indicators: (name, picker) ----------
# picker(i) -> (chosen_ticker, direction_ok) ; returns None if no candidate
def build_indicator(kind):
    def pick(i):
        best=None; bestv=None
        for t in TICKERS:
            cl=COL[t]
            if cl[i] is None: continue
            v=None; ok=True
            if kind=='REV5':   v=ret(cl,i,5);   pref='low'
            elif kind=='REV21':v=ret(cl,i,21);  pref='low'
            elif kind=='MOM126':v=ret(cl,i,126);pref='high'
            elif kind=='MOM252_21':
                a=ret(cl,i,252); b=ret(cl,i,21)
                v=(a-b) if (a is not None and b is not None) else None; pref='high'
            elif kind=='LTREV': v=ret(cl,i,1260); pref='low'
            elif kind=='TREND200':
                m=sma(cl,200,i); v=(cl[i]/m-1) if m else None; pref='high'
            elif kind in ('canary','st','lt','all'):
                sg=signals(cl,i); v=sg[kind] if sg else None; pref='high'
            elif kind=='BUYSCORE':
                sg=signals(cl,i)
                if sg and None not in (sg['canary'],sg['st'],sg['lt'],sg['all']):
                    v=(sg['canary']*1+sg['st']*2+sg['lt']*3+sg['all']*4)/10.0
                pref='high'
            elif kind=='DIPUP':               # above 200dMA and biggest 5d dip
                m=sma(cl,200,i)
                if m and cl[i]>m: v=ret(cl,i,5); pref='low'
            elif kind=='MOMUP':               # 6m momentum but only if above 200dMA
                m=sma(cl,200,i)
                if m and cl[i]>m: v=ret(cl,i,126); pref='high'
            if v is None: continue
            if bestv is None or (pref=='high' and v>bestv) or (pref=='low' and v<bestv):
                bestv=v; best=t
        return best
    return pick

HORIZONS=[('1wk',5),('1mo',21),('6mo',126),('1yr',252),('5yr',1260)]
CANDS={
 '1wk':['REV5','REV21','canary','MOM126','DIPUP','TREND200','all'],
 '1mo':['REV21','DIPUP','canary','st','MOM126','MOMUP','BUYSCORE','TREND200'],
 '6mo':['st','lt','MOM126','MOM252_21','MOMUP','TREND200','BUYSCORE','all'],
 '1yr':['lt','all','MOM252_21','MOM126','MOMUP','BUYSCORE','TREND200'],
 '5yr':['all','lt','MOM252_21','LTREV','TREND200','BUYSCORE','MOMUP'],
}
COST=0.0015*2   # round-trip

# rebalance dates: every 21 trading days, need >=1260 history for fair compare across all horizons
START=1260
def run_indicator(kind, H):
    pick=build_indicator(kind)
    rows=[]   # (date_index, fwd_return_net)
    i=START
    N=len(dates)
    while i+H < N:
        t=pick(i)
        if t is not None:
            r=ret(COL[t], i+H, H)
            if r is not None:
                rows.append((i, r-COST))
        i+=21
    return rows

def ew_null(H):
    # average name: mean forward H-return across all tickers at each rebalance date
    rows=[]; i=START; N=len(dates)
    while i+H<N:
        vs=[]
        for t in TICKERS:
            r=ret(COL[t], i+H, H)
            if r is not None: vs.append(r)
        if vs: rows.append((i, sum(vs)/len(vs)))
        i+=21
    return rows
def spy_null(H):
    rows=[]; i=START; N=len(dates)
    while i+H<N:
        r=ret(SPY, i+H, H)
        if r is not None: rows.append((i,r))
        i+=21
    return rows

def halves(rows):
    if not rows: return (None,None,None,0)
    mid=rows[len(rows)//2][0]
    h1=[r for (d,r) in rows if d< mid]
    h2=[r for (d,r) in rows if d>=mid]
    full=[r for (_,r) in rows]
    m=lambda x: (sum(x)/len(x)) if x else None
    return (m(h1),m(h2),m(full),len(full))
def winrate(rows):
    v=[r for (_,r) in rows];
    return sum(1 for x in v if x>0)/len(v) if v else 0

print('='*90)
print(' PER-HORIZON INDICATOR TEST  — single top pick, monthly rebalance, 15bps/side round-trip')
print(' universe: %d survivor equities 2001-2026 (survivorship => absolute #s optimistic)'%len(TICKERS))
print(' QUALIFY = beat equal-weight null mean in BOTH halves.')
print('='*90)

winners={}
for hz,H in HORIZONS:
    ew=ew_null(H); sp=spy_null(H)
    e1,e2,ef,_=halves(ew); s1,s2,sf,_=halves(sp)
    print('\n### %s hold (%d trading days)  |  EW-null: H1 %+.1f%% H2 %+.1f%% full %+.1f%%  |  SPY: H1 %+.1f%% H2 %+.1f%% full %+.1f%%'
          %(hz,H, e1*100,e2*100,ef*100, s1*100,s2*100,sf*100))
    print('   %-11s %8s %8s %8s %6s  %-4s %-4s'%('indicator','H1','H2','FULL','win%','>EW','>SPY'))
    ranked=[]
    for kind in CANDS[hz]:
        rows=run_indicator(kind,H)
        h1,h2,fu,n=halves(rows); wr=winrate(rows)
        beatEW = (h1 is not None and h1>e1 and h2>e2)
        beatSPY= (h1 is not None and h1>s1 and h2>s2)
        ranked.append((kind,h1,h2,fu,wr,beatEW,beatSPY,n))
        print('   %-11s %+7.1f%% %+7.1f%% %+7.1f%% %5.0f%%   %-3s  %-3s'
              %(kind, h1*100,h2*100,fu*100, wr*100, 'Y' if beatEW else '.', 'Y' if beatSPY else '.'))
    # choose: qualifiers first (beatEW both halves), prefer also beatSPY, then highest full
    quals=[r for r in ranked if r[5]]
    pool = quals if quals else []
    both=[r for r in pool if r[6]]
    chosen=None
    if both: chosen=max(both, key=lambda r:r[3])
    elif pool: chosen=max(pool, key=lambda r:r[3])
    winners[hz]=(chosen, ef, sf)
    if chosen:
        print('   -> WINNER: %s  (full %+.1f%%, win %.0f%%, %s)'
              %(chosen[0], chosen[3]*100, chosen[4]*100, 'beats SPY too' if chosen[6] else 'beats EW only'))
    else:
        print('   -> NO qualifier beat the equal-weight null in both halves. Horizon = NO EDGE (grey).')

print('\n'+'='*90)
print(' SUMMARY (what the cards should say)')
print('='*90)
for hz,H in HORIZONS:
    ch,ef,sf=winners[hz]
    if ch: print(' %-4s: use %-10s  full %+.1f%% / win %.0f%%  vs EW %+.1f%% vs SPY %+.1f%%  [%s]'
                 %(hz,ch[0],ch[3]*100,ch[4]*100,ef*100,sf*100,'edge' if ch[6] else 'beats avg name only'))
    else:  print(' %-4s: NO EDGE — grey card, honest "no reliable selection edge"'%hz)
