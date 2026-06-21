"""
fix-custom-stooq.py — Custom US tickers (PLTR etc.) fail because fetchStooq
only works for tickers in STOOQ_MAP. Fix: try Stooq with .us suffix directly
in the customFailed fallback block, bypassing the map.
Run: python fix-custom-stooq.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── Replace customFailed block with one that tries Stooq .us directly ─────────
OLD_CUSTOM_FAILED = """    // Yahoo Finance fallback for user-added tickers (Custom/ASX/Crypto cls) with no data
    const customFailed=WATCHLIST.filter(a=>['Custom','ASX','HK'].includes(a.cls)&&!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes));
    if(customFailed.length){
      await Promise.all(customFailed.map(async a=>{
        try{
          // ASX tickers: append .AX if not already present
          let sym=a.ticker.replace('.','-');
          if(a.cls==='ASX'&&!sym.endsWith('.AX')&&!sym.endsWith('-AX')) sym=sym+'.AX';
          if(a.cls==='HK'&&!sym.includes('.HK')) sym=sym+'.HK';
          const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?range=2y&interval=1d`,8000);
          if(!res.ok) return;
          const d=await res.json();
          const closes=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
          if(closes.length>=21){
            const sigs=computeSignals(closes);
            const stability=closes.length>=32?computeStabilityState(closes):'stable';
            newData[dataKey(a)]={closes,sigs:sigs?{...sigs,stability}:null,loading:false};
          }
        }catch(e){ console.warn('YF custom fallback',a.ticker,e.message); }
      }));
    }
    // Crypto fallback for user-added Crypto tickers with no data
    const cryptoCustomFailed=WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes));
    if(cryptoCustomFailed.length){
      await Promise.all(cryptoCustomFailed.map(async a=>{
        try{
          const sym=a.ticker+'-USD';
          const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?range=2y&interval=1d`,8000);
          if(!res.ok) return;
          const d=await res.json();
          const closes=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
          if(closes.length>=21){
            const sigs=computeSignals(closes);
            const stability=closes.length>=32?computeStabilityState(closes):'stable';
            newData[dataKey(a)]={closes,sigs:sigs?{...sigs,stability}:null,loading:false};
          }
        }catch(e){ console.warn('YF crypto custom fallback',a.ticker,e.message); }
      }));
    }"""

NEW_CUSTOM_FAILED = """    // Fallback for user-added tickers with no data yet
    const customFailed=WATCHLIST.filter(a=>['Custom','ASX','HK'].includes(a.cls)&&!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes));
    if(customFailed.length){
      await Promise.all(customFailed.map(async a=>{
        let closes=[];
        // Try 1: Stooq with market suffix (bypasses STOOQ_MAP for custom tickers)
        try{
          let stooqSym=a.ticker.toLowerCase();
          if(a.cls==='ASX') stooqSym+='.au';
          else if(a.cls==='HK') stooqSym+='.hk';
          else stooqSym+='.us'; // Default: US market
          const res=await fetchT(`https://stooq.com/q/d/l/?s=${stooqSym}&i=d`,10000);
          if(res.ok){
            const text=await res.text();
            const lines=text.trim().split('\\n').slice(1);
            if(lines.length>0&&!lines[0].startsWith('No data')){
              closes=lines.map(l=>parseFloat(l.split(',')[4])).filter(v=>!isNaN(v)&&v>0).reverse();
            }
          }
        }catch(e){ console.warn('Stooq custom',a.ticker,e.message); }
        // Try 2: Yahoo Finance if Stooq failed
        if(closes.length<21){
          try{
            let yfSym=a.ticker.replace('.','-');
            if(a.cls==='ASX'&&!yfSym.endsWith('.AX')) yfSym+='.AX';
            else if(a.cls==='HK'&&!yfSym.includes('.HK')) yfSym+='.HK';
            const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${yfSym}?range=2y&interval=1d`,8000);
            if(res.ok){
              const d=await res.json();
              const raw=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
              if(raw.length>=21) closes=raw;
            }
          }catch(e){ console.warn('YF custom',a.ticker,e.message); }
        }
        // Try 3: Binance for crypto custom tickers
        if(closes.length<21&&a.cls==='Crypto'){
          const bnCloses=await fetchBinance(a.ticker);
          if(bnCloses.length>=21) closes=bnCloses;
        }
        if(closes.length>=21){
          const sigs=computeSignals(closes);
          const stability=closes.length>=32?computeStabilityState(closes):'stable';
          newData[dataKey(a)]={closes,sigs:sigs?{...sigs,stability}:null,loading:false};
        }
      }));
    }"""

if OLD_CUSTOM_FAILED in content:
    content = content.replace(OLD_CUSTOM_FAILED, NEW_CUSTOM_FAILED, 1)
    changes += 1
    print('✓  customFailed: Stooq .us primary → Yahoo fallback → Binance crypto')
elif 'Stooq with market suffix' in content:
    print('–  Already using Stooq direct')
else:
    print('✗  customFailed block not matched')
    idx = content.find('customFailed=WATCHLIST')
    if idx != -1: print(repr(content[idx:idx+200]))

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
