"""
fix-custom-av-news.py — Two fixes:
1. Custom ticker fallback: uses Alpha Vantage TIME_SERIES_DAILY for US stocks
   when TD/Yahoo/Stooq all fail. AV is guaranteed to work (already used for ASX/HK).
2. Crypto news: adds Finnhub crypto category news to crypto ticker rows.
Run: python fix-custom-av-news.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Add AV fallback inside customFailed for Custom cls tickers ─────────────
# Find the end of the Stooq .us try block and Yahoo try block, then add AV
OLD_CUSTOM_BLOCK_END = """        // Try 3: Binance for crypto custom tickers
        if(closes.length<21&&a.cls==='Crypto'){
          const bnCloses=await fetchBinance(a.ticker);
          if(bnCloses.length>=21) closes=bnCloses;
        }
        if(closes.length>=21){"""

NEW_CUSTOM_BLOCK_END = """        // Try 3: Binance for crypto custom tickers
        if(closes.length<21&&a.cls==='Crypto'){
          const bnCloses=await fetchBinance(a.ticker);
          if(bnCloses.length>=21) closes=bnCloses;
        }
        // Try 4: Alpha Vantage for Custom US stock tickers (reliable, already in app)
        if(closes.length<21&&a.cls==='Custom'&&avKey){
          try{
            const res=await fetchT(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${a.ticker}&outputsize=full&apikey=${avKey}`,15000);
            if(res.ok){
              const json=await res.json();
              const ts=json['Time Series (Daily)'];
              if(ts){
                closes=Object.entries(ts).sort(([a],[b])=>a>b?1:-1).map(([,v])=>parseFloat(v['4. close'])).filter(v=>!isNaN(v));
              }
            }
          }catch(e){ console.warn('AV custom fallback',a.ticker,e.message); }
        }
        if(closes.length>=21){"""

if OLD_CUSTOM_BLOCK_END in content:
    content = content.replace(OLD_CUSTOM_BLOCK_END, NEW_CUSTOM_BLOCK_END, 1)
    changes += 1
    print('✓  Alpha Vantage fallback added for custom US stock tickers')
elif 'AV custom fallback' in content:
    print('–  AV fallback already present')
else:
    print('✗  customFailed end block not matched')
    idx = content.find('Binance for crypto custom')
    if idx != -1: print(repr(content[idx:idx+200]))

# ── 2. Add crypto news via Finnhub crypto category ────────────────────────────
# Find the existing AV news fetch block (fire-and-forget) and add crypto news
OLD_AV_NEWS = "(async () => { for (const {ticker,avSym} of AV_INTL_MAP)"
# Add Finnhub crypto news fire-and-forget right after setData(newData)
OLD_SET_DATA = "setData(newData); setLastFetch(new Date());"
NEW_SET_DATA = """setData(newData); setLastFetch(new Date());

    // Crypto news via Finnhub (fire-and-forget, same key already in app)
    (async () => {
      try {
        const fhK = typeof FH_KEY_DEFAULT !== 'undefined' ? FH_KEY_DEFAULT : '';
        if (!fhK) return;
        const res = await fetchT(`https://finnhub.io/api/v1/news?category=crypto&token=${fhK}`, 8000);
        if (!res.ok) return;
        const items = await res.json();
        if (!Array.isArray(items) || !items.length) return;
        // Build per-ticker sentiment from recent headlines mentioning the ticker name/symbol
        const cryptoTickers = WATCHLIST.filter(a => a.cls === 'Crypto').map(a => a.ticker);
        setData(prev => {
          const next = { ...prev };
          cryptoTickers.forEach(t => {
            const key = t + '__Crypto';
            if (!next[key]) return;
            // Find articles mentioning this ticker or its name
            const relevant = items.filter(item => {
              const text = (item.headline + ' ' + (item.summary||'')).toLowerCase();
              return text.includes(t.toLowerCase());
            });
            const src = relevant.length ? relevant : items.slice(0, 3);
            if (!src.length) return;
            // Simple sentiment: positive words vs negative
            const pos = ['bull', 'surge', 'rally', 'gain', 'rise', 'high', 'pump', 'moon', 'break', 'ath'];
            const neg = ['bear', 'drop', 'fall', 'crash', 'dump', 'low', 'sell', 'down', 'weak', 'fear'];
            let score = 0;
            src.forEach(item => {
              const txt = (item.headline + ' ' + (item.summary||'')).toLowerCase();
              pos.forEach(w => { if (txt.includes(w)) score++; });
              neg.forEach(w => { if (txt.includes(w)) score--; });
            });
            const sentiment = score > 1 ? 0.6 : score < -1 ? -0.6 : score * 0.3;
            const headline = src[0]?.headline || '';
            const url = src[0]?.url || '';
            next[key] = { ...next[key], news: { sentiment, headline, url, source: 'Finnhub' } };
          });
          return next;
        });
      } catch(e) { console.warn('Crypto news:', e.message); }
    })();"""

if OLD_SET_DATA in content and 'Crypto news via Finnhub' not in content:
    content = content.replace(OLD_SET_DATA, NEW_SET_DATA, 1)
    changes += 1
    print('✓  Finnhub crypto news (fire-and-forget) added')
elif 'Crypto news via Finnhub' in content:
    print('–  Crypto news already added')
else:
    print('✗  setData anchor not matched')
    idx = content.find('setData(newData)')
    if idx != -1: print(repr(content[idx:idx+60]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
