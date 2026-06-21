"""
fix-crypto-primary.py — Swaps crypto fetch to Yahoo Finance first (batched,
10 at a time with 300ms delay), CoinCap as fallback. Eliminates the 46-parallel-
request rate limit problem.
Run: python fix-crypto-primary.py  then: (also run fix-add-button.py)
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

OLD_CRYPTO_BLOCK = """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
    const cryptoFetches=await Promise.all(cryptoAssets.map(t=>fetchCoinCap(CRYPTO_COINCAP_IDS[t]||t.toLowerCase())));
    const cryptoMap=Object.fromEntries(cryptoAssets.map((t,i)=>[t,cryptoFetches[i]||[]]));

    // Yahoo Finance fallback for crypto tickers with no data from CoinCap/CoinGecko
    const failedCrypto=cryptoAssets.filter(t=>!(cryptoMap[t]&&cryptoMap[t].length>=21));
    if(failedCrypto.length){
      await Promise.all(failedCrypto.map(async t=>{
        try{
          const sym=t+'-USD';
          const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?range=2y&interval=1d`,8000);
          if(!res.ok) return;
          const d=await res.json();
          const closes=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
          if(closes.length>=21) cryptoMap[t]=closes;
        }catch(e){ console.warn('YF crypto fallback',t,e.message); }
      }));
    }

    """

NEW_CRYPTO_BLOCK = """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
    const cryptoMap={};

    // Primary: Yahoo Finance (batched 10 at a time to avoid rate limits)
    for(let _ci=0;_ci<cryptoAssets.length;_ci+=10){
      const _batch=cryptoAssets.slice(_ci,_ci+10);
      await Promise.all(_batch.map(async t=>{
        try{
          const sym=t+'-USD';
          const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?range=2y&interval=1d`,8000);
          if(!res.ok) return;
          const d=await res.json();
          const closes=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
          if(closes.length>=21) cryptoMap[t]=closes;
        }catch(e){ console.warn('YF crypto',t,e.message); }
      }));
      if(_ci+10<cryptoAssets.length) await new Promise(r=>setTimeout(r,300));
    }

    // Fallback: CoinCap for any Yahoo missed
    const _coinCapMissed=cryptoAssets.filter(t=>!(cryptoMap[t]&&cryptoMap[t].length>=21));
    if(_coinCapMissed.length){
      const _ccFetches=await Promise.all(_coinCapMissed.map(t=>fetchCoinCap(CRYPTO_COINCAP_IDS[t]||t.toLowerCase())));
      _coinCapMissed.forEach((t,i)=>{ if(_ccFetches[i]&&_ccFetches[i].length>=21) cryptoMap[t]=_ccFetches[i]; });
    }

    """

if OLD_CRYPTO_BLOCK in content:
    content = content.replace(OLD_CRYPTO_BLOCK, NEW_CRYPTO_BLOCK, 1)
    changes += 1
    print('✓  Crypto fetch: Yahoo Finance primary (batched), CoinCap fallback')
elif 'Yahoo Finance (batched' in content:
    print('–  Batched Yahoo already in place')
else:
    print('✗  Old crypto block not matched')
    idx = content.find('cryptoAssets=')
    if idx != -1: print(repr(content[idx:idx+150]))

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced.')
print('Now run: python fix-add-button.py  then: .\\git-push.bat')
