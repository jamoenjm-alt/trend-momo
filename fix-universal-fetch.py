"""
fix-universal-fetch.py — Replaces the customFailed block with a universal
multi-source fetch that tries every available API for ANY ticker type:
  1. Binance (crypto: TICKERUSDT)
  2. CoinCap (crypto alt)
  3. Alpha Vantage US stock
  4. Alpha Vantage with .AUS suffix (ASX)
  5. Alpha Vantage with .HKG suffix (HK)
Works for US stocks, ASX, HK, crypto — anything the user types in.
Run: python fix-universal-fetch.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Find and replace the entire customFailed block
# It starts with "// Fallback for user-added tickers" and ends before the ASX loop
OLD_BLOCK_START = "    // Fallback for user-added tickers with no data yet\n    const customFailed=WATCHLIST.filter(a=>['Custom','ASX','HK'].includes(a.cls)&&!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes));"

# Find start
start_idx = content.find(OLD_BLOCK_START)
if start_idx == -1:
    # Try alternate version from fix-custom-av-news.py
    OLD_BLOCK_START = "    // Yahoo Finance fallback for user-added tickers (Custom/ASX/Crypto cls) with no data\n    const customFailed="
    start_idx = content.find(OLD_BLOCK_START)

# Find end: the ASX/HK loop that follows
end_marker = "for (const a of WATCHLIST.filter(a=>(a.cls==='ASX'||a.cls==='HK')&&!staticData[a.ticker]))"
end_idx = content.find(end_marker, start_idx if start_idx != -1 else 0)

if start_idx == -1 or end_idx == -1:
    print(f'✗ Could not locate customFailed block (start={start_idx}, end={end_idx})')
    # Show context
    idx = content.find('customFailed')
    if idx != -1: print(repr(content[max(0,idx-50):idx+200]))
    sys.exit(1)

OLD_BLOCK = content[start_idx:end_idx]
print(f'Found block to replace: {len(OLD_BLOCK)} chars')

NEW_BLOCK = """    // Universal fallback: tries every available source for ANY user-added ticker
    const customFailed=WATCHLIST.filter(a=>!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes)&&['Custom','ASX','HK','Crypto','Watch','Top20'].includes(a.cls)&&!cryptoMap[a.ticker]);
    if(customFailed.length){
      await Promise.all(customFailed.map(async a=>{
        let closes=[];
        const t=a.ticker;
        const isCrypto=a.cls==='Crypto';
        const isASX=a.cls==='ASX'||t.endsWith('.AX');
        const isHK=a.cls==='HK'||t.endsWith('.HK');

        // 1. Binance (crypto, no key, fast)
        if(isCrypto&&closes.length<21){
          closes=await fetchBinance(t);
        }

        // 2. CoinCap (crypto alt)
        if(isCrypto&&closes.length<21){
          const cc=await fetchCoinCap(CRYPTO_COINCAP_IDS[t]||t.toLowerCase());
          if(cc.length>=21) closes=cc;
        }

        // 3. Yahoo Finance -USD (crypto last resort)
        if(isCrypto&&closes.length<21){
          try{
            const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${t}-USD?range=2y&interval=1d`,8000);
            if(res.ok){
              const d=await res.json();
              const raw=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
              if(raw.length>=21) closes=raw;
            }
          }catch{}
        }

        // 4. Alpha Vantage — US stock (works for most global exchanges too)
        if(!isCrypto&&closes.length<21&&avKey){
          try{
            const res=await fetchT(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${t}&outputsize=full&apikey=${avKey}`,15000);
            if(res.ok){
              const json=await res.json();
              const ts=json['Time Series (Daily)'];
              if(ts) closes=Object.entries(ts).sort(([a],[b])=>a>b?1:-1).map(([,v])=>parseFloat(v['4. close'])).filter(v=>!isNaN(v));
            }
          }catch(e){ console.warn('AV fallback',t,e.message); }
        }

        // 5. Alpha Vantage with .AUS suffix (ASX tickers)
        if(isASX&&closes.length<21&&avKey){
          try{
            const avSym=t.replace('.AX','')+'.AUS';
            const res=await fetchT(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${avSym}&outputsize=full&apikey=${avKey}`,15000);
            if(res.ok){
              const json=await res.json();
              const ts=json['Time Series (Daily)'];
              if(ts) closes=Object.entries(ts).sort(([a],[b])=>a>b?1:-1).map(([,v])=>parseFloat(v['4. close'])).filter(v=>!isNaN(v));
            }
          }catch{}
        }

        // 6. Alpha Vantage with .HKG suffix (HK tickers)
        if(isHK&&closes.length<21&&avKey){
          try{
            const avSym=t.replace('.HK','')+'.HKG';
            const res=await fetchT(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${avSym}&outputsize=full&apikey=${avKey}`,15000);
            if(res.ok){
              const json=await res.json();
              const ts=json['Time Series (Daily)'];
              if(ts) closes=Object.entries(ts).sort(([a],[b])=>a>b?1:-1).map(([,v])=>parseFloat(v['4. close'])).filter(v=>!isNaN(v));
            }
          }catch{}
        }

        if(closes.length>=21){
          const sigs=computeSignals(closes);
          const stability=closes.length>=32?computeStabilityState(closes):'stable';
          newData[dataKey(a)]={closes,sigs:sigs?{...sigs,stability}:null,loading:false};
        }
      }));
    }
    """ + end_marker

content = content[:start_idx] + NEW_BLOCK + content[end_idx + len(end_marker):]
changes += 1
print('✓  Universal multi-source fetch block applied')
print('   Sources: Binance → CoinCap → AV US → AV .AUS → AV .HKG')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
