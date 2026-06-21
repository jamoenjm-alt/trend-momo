"""
fix-crypto-binance.py — Adds Binance public API as primary crypto source.
No API key, 1200 req/min limit, excellent CORS, covers all major coins.
Fetch order: Binance → CoinCap → Yahoo Finance
Run: python fix-crypto-binance.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Add fetchBinance function right before fetchCoinCap ────────────────────
OLD_FETCHCOINCAP = "    const fetchCoinCap = async (coinId) => {"
NEW_FETCHCOINCAP = """    const fetchBinance = async (ticker) => {
      // Some coins use different Binance symbols
      const BN_MAP = { BNB:'BNB', MATIC:'MATIC', WBTC:'WBTC' };
      try {
        const sym = (BN_MAP[ticker] || ticker) + 'USDT';
        const res = await fetchT(`https://api.binance.com/api/v3/klines?symbol=${sym}&interval=1d&limit=500`, 8000);
        if (!res.ok) return [];
        const data = await res.json();
        if (!Array.isArray(data) || !data.length) return [];
        return data.map(k => parseFloat(k[4])).filter(v => !isNaN(v));
      } catch(e) { console.warn('Binance', ticker, e.message); return []; }
    };

    const fetchCoinCap = async (coinId) => {"""

if OLD_FETCHCOINCAP in content and 'fetchBinance' not in content:
    content = content.replace(OLD_FETCHCOINCAP, NEW_FETCHCOINCAP, 1)
    changes += 1
    print('✓  fetchBinance function added')
elif 'fetchBinance' in content:
    print('–  fetchBinance already present')
else:
    print('✗  fetchCoinCap anchor not found')
    idx = content.find('fetchCoinCap')
    if idx != -1: print(repr(content[idx:idx+60]))

# ── 2. Replace the crypto fetch block with Binance → CoinCap → Yahoo chain ───
# Handle both versions (batched CoinCap or Yahoo-primary)
OLD_BLOCKS = [
    # Version A: batched CoinCap (from fix-crypto-coincap-batched.py)
    """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
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

    """,
    # Version B: original CoinCap-all-at-once + failedCrypto fallback
    """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
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

    """,
]

NEW_CRYPTO_BLOCK = """const cryptoAssets=[...new Set(WATCHLIST.filter(a=>a.cls==='Crypto'&&!staticData[a.ticker]).map(a=>a.ticker))];
    const cryptoMap={};

    // 1st: Binance public API — no key, 1200 req/min, best coverage
    await Promise.all(cryptoAssets.map(async t=>{
      const closes=await fetchBinance(t);
      if(closes.length>=21) cryptoMap[t]=closes;
    }));

    // 2nd: CoinCap for anything Binance missed (TRX, TON, some alts)
    const _ccMiss=cryptoAssets.filter(t=>!(cryptoMap[t]&&cryptoMap[t].length>=21));
    if(_ccMiss.length){
      const _ccF=await Promise.all(_ccMiss.map(t=>fetchCoinCap(CRYPTO_COINCAP_IDS[t]||t.toLowerCase())));
      _ccMiss.forEach((t,i)=>{ if(_ccF[i]&&_ccF[i].length>=21) cryptoMap[t]=_ccF[i]; });
    }

    // 3rd: Yahoo Finance (-USD) last resort
    const _yfMiss=cryptoAssets.filter(t=>!(cryptoMap[t]&&cryptoMap[t].length>=21));
    if(_yfMiss.length){
      await Promise.all(_yfMiss.map(async t=>{
        try{
          const res=await fetchT(`https://query1.finance.yahoo.com/v8/finance/chart/${t}-USD?range=2y&interval=1d`,8000);
          if(!res.ok) return;
          const d=await res.json();
          const closes=(d.chart?.result?.[0]?.indicators?.quote?.[0]?.close||[]).filter(v=>v!=null&&!isNaN(v));
          if(closes.length>=21) cryptoMap[t]=closes;
        }catch(e){}
      }));
    }

    """

applied = False
for old in OLD_BLOCKS:
    if old in content:
        content = content.replace(old, NEW_CRYPTO_BLOCK, 1)
        changes += 1
        print('✓  Crypto fetch: Binance → CoinCap → Yahoo chain')
        applied = True
        break

if not applied:
    if 'fetchBinance(t)' in content:
        print('–  Binance chain already in place')
    else:
        print('✗  Crypto block not matched — check which version is in the file')
        idx = content.find('cryptoAssets=')
        if idx != -1: print(repr(content[idx:idx+200]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
