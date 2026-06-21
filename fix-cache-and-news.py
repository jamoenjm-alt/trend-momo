"""
fix-cache-and-news.py — Three fixes:
1. Cache custom ticker prices in localStorage (AV only called once per ticker,
   not on every page reload — stops AV daily limit from being exhausted)
2. Fix crypto news: update setNewsData instead of setData
3. Fix X button: looser textContent matching for React-rendered cells
Run: python fix-cache-and-news.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Inject cache read at loadAll start (after staticData build) ────────────
OLD_STATIC_BUILD = """    const staticData = {};
    for (const a of WATCHLIST) { if (window.STATIC_PRICES?.[a.ticker]?.length) staticData[a.ticker] = window.STATIC_PRICES[a.ticker]; }"""

NEW_STATIC_BUILD = """    const staticData = {};
    for (const a of WATCHLIST) { if (window.STATIC_PRICES?.[a.ticker]?.length) staticData[a.ticker] = window.STATIC_PRICES[a.ticker]; }
    // Load cached prices for custom tickers (avoids repeated AV calls)
    const CACHE_TTL = 20 * 60 * 60 * 1000; // 20 hours
    for (const a of WATCHLIST.filter(a => !staticData[a.ticker])) {
      try {
        const cached = JSON.parse(localStorage.getItem('pc_' + a.ticker) || 'null');
        if (cached && Date.now() - cached.ts < CACHE_TTL && cached.c && cached.c.length >= 21) {
          staticData[a.ticker] = cached.c;
        }
      } catch {}
    }"""

if OLD_STATIC_BUILD in content and 'CACHE_TTL' not in content:
    content = content.replace(OLD_STATIC_BUILD, NEW_STATIC_BUILD, 1)
    changes += 1
    print('✓  Price cache read injected at loadAll start')
elif 'CACHE_TTL' in content:
    print('–  Cache read already present')
else:
    print('✗  staticData build not matched')

# ── 2. Save to cache after successful custom fetch ────────────────────────────
OLD_SAVE = """        if(closes.length>=21){
          const sigs=computeSignals(closes);
          const stability=closes.length>=32?computeStabilityState(closes):'stable';
          newData[dataKey(a)]={closes,sigs:sigs?{...sigs,stability}:null,loading:false};
        }
      }));
    }"""

NEW_SAVE = """        if(closes.length>=21){
          // Cache result so AV isn't called again on next page load
          try { localStorage.setItem('pc_'+t, JSON.stringify({c:closes.slice(-400), ts:Date.now()})); } catch {}
          const sigs=computeSignals(closes);
          const stability=closes.length>=32?computeStabilityState(closes):'stable';
          newData[dataKey(a)]={closes,sigs:sigs?{...sigs,stability}:null,loading:false};
        }
      }));
    }"""

if OLD_SAVE in content and 'localStorage.setItem(\'pc_\'' not in content:
    content = content.replace(OLD_SAVE, NEW_SAVE, 1)
    changes += 1
    print('✓  Price cache write added after successful fetch')
elif 'localStorage.setItem(\'pc_\'' in content:
    print('–  Cache write already present')
else:
    print('✗  customFailed save block not matched')

# ── 3. Fix crypto news: call setNewsData not setData ─────────────────────────
OLD_NEWS_SET = """        setData(prev => {
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
        });"""

NEW_NEWS_SET = """        // Build newsData entries for crypto tickers
        const cryptoNewsUpdate = {};
        const pos = ['bull', 'surge', 'rally', 'gain', 'rise', 'high', 'pump', 'moon', 'break', 'ath'];
        const neg = ['bear', 'drop', 'fall', 'crash', 'dump', 'low', 'sell', 'down', 'weak', 'fear'];
        cryptoTickers.forEach(t => {
          const relevant = items.filter(item => {
            const text = (item.headline + ' ' + (item.summary||'')).toLowerCase();
            return text.includes(t.toLowerCase());
          });
          const src = relevant.length ? relevant : items.slice(0, 3);
          if (!src.length) return;
          let score = 0;
          src.forEach(item => {
            const txt = (item.headline + ' ' + (item.summary||'')).toLowerCase();
            pos.forEach(w => { if (txt.includes(w)) score++; });
            neg.forEach(w => { if (txt.includes(w)) score--; });
          });
          const sentiment = score > 1 ? 0.6 : score < -1 ? -0.6 : score * 0.3;
          cryptoNewsUpdate[t] = {
            sentiment,
            label: sentiment > 0.3 ? 'Bullish' : sentiment < -0.3 ? 'Bearish' : 'Neutral',
            headline: src[0]?.headline || '',
            url: src[0]?.url || ''
          };
        });
        if (Object.keys(cryptoNewsUpdate).length) {
          setNewsData(prev => ({ ...(prev||{}), ...cryptoNewsUpdate }));
        }"""

if OLD_NEWS_SET in content:
    content = content.replace(OLD_NEWS_SET, NEW_NEWS_SET, 1)
    changes += 1
    print('✓  Crypto news: now calls setNewsData with correct shape')
elif 'setNewsData(prev =>' in content:
    print('–  setNewsData already targeted')
else:
    print('✗  Old setData news block not matched')
    idx = content.find('cryptoTickers.forEach')
    if idx != -1: print(repr(content[idx:idx+100]))

# ── 4. Fix X button: use startsWith instead of exact match ───────────────────
OLD_TICKER_MATCH = "      if (customTickers.indexOf(tickerText) !== -1 && !row.querySelector('.ct-row-del')) {"
NEW_TICKER_MATCH = """      // Match: textContent may include extra React-rendered text, check if it starts with or equals the ticker
      var matchedTicker = customTickers.find(function(tk) {
        return tickerText === tk || tickerText.startsWith(tk + ' ') || tickerText.startsWith(tk + '\\n');
      });
      if (matchedTicker && !row.querySelector('.ct-row-del')) {"""

OLD_BTN_TICKER = "        btn.title = 'Remove ' + tickerText;"
NEW_BTN_TICKER = "        btn.title = 'Remove ' + matchedTicker;"

OLD_DELETE_CALL = "          if (confirm('Remove ' + tickerText + '?')) deleteTicker(tickerText);"
NEW_DELETE_CALL = "          if (confirm('Remove ' + matchedTicker + '?')) deleteTicker(matchedTicker);"

if OLD_TICKER_MATCH in content:
    content = content.replace(OLD_TICKER_MATCH, NEW_TICKER_MATCH, 1)
    content = content.replace(OLD_BTN_TICKER, NEW_BTN_TICKER, 1)
    content = content.replace(OLD_DELETE_CALL, NEW_DELETE_CALL, 1)
    changes += 1
    print('✓  X button: looser ticker matching (startsWith)')
elif 'matchedTicker' in content:
    print('–  Ticker matching already updated')
else:
    print('✗  X button ticker match not found')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
