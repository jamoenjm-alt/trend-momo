"""
fix-crypto-coincap-batched.py — Reverts to CoinCap as primary for crypto
but batches requests (8 at a time, 500ms gap) to avoid rate limits.
Yahoo Finance remains as fallback for anything CoinCap misses.
Run: python fix-crypto-coincap-batched.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

OLD_BLOCK = """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
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

NEW_BLOCK = """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
    const cryptoMap={};

    // Primary: CoinCap batched (8 per batch, 500ms gap) to avoid rate limits
    for(let _ci=0;_ci<cryptoAssets.length;_ci+=8){
      const _batch=cryptoAssets.slice(_ci,_ci+8);
      const _fetches=await Promise.all(_batch.map(t=>fetchCoinCap(CRYPTO_COINCAP_IDS[t]||t.toLowerCase())));
      _batch.forEach((t,i)=>{ if(_fetches[i]&&_fetches[i].length>=21) cryptoMap[t]=_fetches[i]; });
      if(_ci+8<cryptoAssets.length) await new Promise(r=>setTimeout(r,500));
    }

    // Fallback: Yahoo Finance (-USD) for anything CoinCap missed
    const _yfMissed=cryptoAssets.filter(t=>!(cryptoMap[t]&&cryptoMap[t].length>=21));
    if(_yfMissed.length){
      await Promise.all(_yfMissed.map(async t=>{
        try{
          const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${t}-USD?range=2y&interval=1d`,8000);
          if(!res.ok) return;
          const d=await res.json();
          const closes=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
          if(closes.length>=21) cryptoMap[t]=closes;
        }catch(e){ console.warn('YF crypto fallback',t,e.message); }
      }));
    }

    """

if OLD_BLOCK in content:
    content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)
    changes += 1
    print('✓  Crypto: CoinCap batched primary + Yahoo Finance fallback')
elif 'CoinCap batched' in content:
    print('–  Already using batched CoinCap')
else:
    print('✗  Block not matched')
    idx = content.find('cryptoAssets=')
    if idx != -1: print(repr(content[idx:idx+200]))

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
