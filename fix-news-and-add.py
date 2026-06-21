"""
fix-news-and-add.py — Two fixes:
1. Crypto news: store 'Bullish'/'Bearish'/'Neutral' string (not object) in newsData
   so NEWS_BADGE[s] lookup works in NewsCell
2. Custom ticker add: expose window._fetchTicker from module scope (has access to
   module-level fetchT + TD_KEY/AV_KEY_DEFAULT), so vanilla go() uses exact same
   fetch logic as the main app
Run: python fix-news-and-add.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Fix crypto news: store label string, not object ────────────────────────
OLD_CRYPTO_NEWS_OBJ = """          cryptoNewsUpdate[t] = {
            sentiment,
            label: sentiment > 0.3 ? 'Bullish' : sentiment < -0.3 ? 'Bearish' : 'Neutral',
            headline: src[0]?.headline || '',
            url: src[0]?.url || ''
          };"""

NEW_CRYPTO_NEWS_OBJ = """          // NewsCell reads newsData[ticker] as a string key into NEWS_BADGE
          cryptoNewsUpdate[t] = sentiment > 0.3 ? 'Bullish' : sentiment < -0.3 ? 'Bearish' : 'Neutral';"""

if OLD_CRYPTO_NEWS_OBJ in content:
    content = content.replace(OLD_CRYPTO_NEWS_OBJ, NEW_CRYPTO_NEWS_OBJ, 1)
    changes += 1
    print('✓  Crypto news: now stores label string (Bullish/Bearish/Neutral)')
elif "cryptoNewsUpdate[t] = sentiment" in content:
    print('–  Crypto news label already a string')
else:
    print('✗  Crypto news object not matched')

# ── 2. Inject window._fetchTicker into module scope after window._KEYS ────────
OLD_KEYS_INJECT = "window._KEYS={td:TD_KEY,av:AV_KEY_DEFAULT};"

NEW_KEYS_INJECT = """window._KEYS={td:TD_KEY,av:AV_KEY_DEFAULT};
  // Expose ticker fetch to vanilla scripts (add-bar handler)
  window._fetchTicker = async function(ticker) {
    let closes = [];
    let cls = null;
    const sym = ticker.toUpperCase();
    // 1. Twelve Data (module-level fetchT has proper timeout/abort)
    try {
      const r = await fetchT(`https://api.twelvedata.com/time_series?symbol=${sym}&interval=1day&outputsize=300&apikey=${TD_KEY}`, 8000);
      if (r && r.ok) {
        const d = await r.json();
        if (d.values && d.values.length >= 21)
          closes = d.values.map(v => parseFloat(v.close)).filter(v => !isNaN(v)).reverse();
      }
    } catch(e) { console.warn('_fetchTicker TD', sym, e.message); }
    // 2. Binance (crypto, no key)
    if (closes.length < 21) {
      try {
        const r2 = await fetch(`https://api.binance.com/api/v3/klines?symbol=${sym}USDT&interval=1d&limit=300`);
        if (r2.ok) {
          const d2 = await r2.json();
          if (Array.isArray(d2) && d2.length >= 21) {
            closes = d2.map(k => parseFloat(k[4])).filter(v => !isNaN(v));
            cls = 'Crypto';
          }
        }
      } catch(e) {}
    }
    // 3. Alpha Vantage
    if (closes.length < 21) {
      try {
        const r3 = await fetchT(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${sym}&outputsize=full&apikey=${AV_KEY_DEFAULT}`, 15000);
        if (r3 && r3.ok) {
          const d3 = await r3.json();
          const ts = d3['Time Series (Daily)'];
          if (ts) closes = Object.entries(ts).sort((a,b)=>a[0]>b[0]?1:-1).map(e=>parseFloat(e[1]['4. close'])).filter(v=>!isNaN(v));
        }
      } catch(e) { console.warn('_fetchTicker AV', sym, e.message); }
    }
    return { closes, cls };
  };"""

if OLD_KEYS_INJECT in content and 'window._fetchTicker' not in content:
    content = content.replace(OLD_KEYS_INJECT, NEW_KEYS_INJECT, 1)
    changes += 1
    print('✓  window._fetchTicker exposed from module scope')
elif 'window._fetchTicker' in content:
    print('–  window._fetchTicker already present')
else:
    print('✗  window._KEYS injection point not found')

# ── 3. Rewrite vanilla go() to use window._fetchTicker ───────────────────────
OLD_GO_ASYNC = """    async function go() {
      var t = inp.value.trim().toUpperCase().replace(/[^A-Z0-9.\\-]/g,'');
      if (!t) return;
      var list = [];
      try { list = JSON.parse(localStorage.getItem('customTickers')||'[]'); } catch{}
      if (list.some(function(x){return x.ticker===t;})) { inp.value=''; return; }
      var cls = (window._snavFilter && window._snavFilter!=='all') ? window._snavFilter : 'Custom';
      var keys = window._KEYS || {};
      var tdKey = keys.td || '';
      var avKey = keys.av || '';
      var closes = [];
      btn.disabled = true;
      var statusEl = document.getElementById('custom-ticker-status');
      if(statusEl) statusEl.textContent = 'Fetching '+t+'...';
      function ft(url, ms) {
        var c = new AbortController();
        var id = setTimeout(function(){c.abort();}, ms||8000);
        return fetch(url, {signal:c.signal}).finally(function(){clearTimeout(id);});
      }
      if (tdKey && closes.length < 21) {
        try {
          var r = await ft('https://api.twelvedata.com/time_series?symbol='+t+'&interval=1day&outputsize=300&apikey='+tdKey);
          if (r.ok) { var d = await r.json(); if (d.values && d.values.length >= 21) closes = d.values.map(function(v){return parseFloat(v.close);}).filter(function(v){return !isNaN(v);}).reverse(); }
        } catch(e) {}
      }
      if (closes.length < 21) {
        try {
          var r2 = await ft('https://api.binance.com/api/v3/klines?symbol='+t+'USDT&interval=1d&limit=300');
          if (r2.ok) { var d2 = await r2.json(); if (Array.isArray(d2) && d2.length >= 21) { closes = d2.map(function(k){return parseFloat(k[4]);}).filter(function(v){return !isNaN(v);}); cls='Crypto'; } }
        } catch(e) {}
      }
      if (closes.length < 21 && avKey) {
        try {
          var r3 = await ft('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+t+'&outputsize=full&apikey='+avKey, 15000);
          if (r3.ok) { var d3 = await r3.json(); var ts = d3['Time Series (Daily)']; if (ts) closes = Object.entries(ts).sort(function(a,b){return a[0]>b[0]?1:-1;}).map(function(e){return parseFloat(e[1]['4. close']);}).filter(function(v){return !isNaN(v);}); }
        } catch(e) {}
      }
      btn.disabled = false;
      if (closes.length < 21) {
        if(statusEl) { statusEl.textContent='\\u2717 No data found for '+t; setTimeout(function(){statusEl.textContent='';},5000); }
        return;
      }
      try { localStorage.setItem('pc_'+t, JSON.stringify({c:closes.slice(-400), ts:Date.now()})); } catch {}
      list.push({ticker:t, name:t, cls:cls});
      localStorage.setItem('customTickers', JSON.stringify(list));
      if(statusEl) statusEl.textContent = '\\u2713 '+t+' added!';
      setTimeout(function(){ location.reload(); }, 300);
    }"""

NEW_GO_ASYNC = """    async function go() {
      var t = inp.value.trim().toUpperCase().replace(/[^A-Z0-9.\\-]/g,'');
      if (!t) return;
      var list = [];
      try { list = JSON.parse(localStorage.getItem('customTickers')||'[]'); } catch{}
      if (list.some(function(x){return x.ticker===t;})) { inp.value=''; return; }
      var cls = (window._snavFilter && window._snavFilter!=='all') ? window._snavFilter : 'Custom';
      btn.disabled = true;
      var statusEl = document.getElementById('custom-ticker-status');
      if(statusEl) statusEl.textContent = 'Fetching '+t+'...';
      var result = { closes: [], cls: null };
      try {
        if (window._fetchTicker) {
          result = await window._fetchTicker(t);
        }
      } catch(e) { console.warn('_fetchTicker failed', t, e.message); }
      btn.disabled = false;
      if (!result.closes || result.closes.length < 21) {
        if(statusEl) { statusEl.textContent='\\u2717 No data found for '+t; setTimeout(function(){statusEl.textContent='';},5000); }
        return;
      }
      if (result.cls) cls = result.cls;
      try { localStorage.setItem('pc_'+t, JSON.stringify({c:result.closes.slice(-400), ts:Date.now()})); } catch {}
      list.push({ticker:t, name:t, cls:cls});
      localStorage.setItem('customTickers', JSON.stringify(list));
      if(statusEl) statusEl.textContent = '\\u2713 '+t+' added!';
      setTimeout(function(){ location.reload(); }, 300);
    }"""

if OLD_GO_ASYNC in content:
    content = content.replace(OLD_GO_ASYNC, NEW_GO_ASYNC, 1)
    changes += 1
    print('✓  Backup go() now delegates to window._fetchTicker')
elif 'window._fetchTicker' in content and 'await window._fetchTicker' in content:
    print('–  go() already delegates to window._fetchTicker')
else:
    print('✗  async go() not matched (may already be correct)')

# ── 4. Same for main doAdd ────────────────────────────────────────────────────
OLD_DOADD_ASYNC = """    async function doAdd() {
      var ticker = input.value.trim().toUpperCase().replace(/[^A-Z0-9.\\-]/g, '');
      if (!ticker) return;
      var list = getCustomTickers();
      if (list.find(function(t) { return t.ticker === ticker; })) {
        status.textContent = ticker + ' already added';
        setTimeout(function() { status.textContent = ''; }, 2000);
        return;
      }
      var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
      var keys = window._KEYS || {};
      var tdKey = keys.td || '';
      var avKey = keys.av || '';
      var closes = [];
      btn.disabled = true;
      status.textContent = 'Fetching ' + ticker + '...';
      function ft(url, ms) {
        var c = new AbortController();
        var id = setTimeout(function(){c.abort();}, ms||8000);
        return fetch(url, {signal:c.signal}).finally(function(){clearTimeout(id);});
      }
      // 1. Twelve Data (module-level fetchT has proper timeout/abort)
      if (tdKey && closes.length < 21) {
        try {
          var r = await ft('https://api.twelvedata.com/time_series?symbol='+ticker+'&interval=1day&outputsize=300&apikey='+tdKey);
          if (r.ok) {
            var d = await r.json();
            if (d.values && d.values.length >= 21)
              closes = d.values.map(function(v){return parseFloat(v.close);}).filter(function(v){return !isNaN(v);}).reverse();
          }
        } catch(e) { console.warn('TD add',ticker,e.message); }
      }
      // 2. Binance — crypto (TICKERUSDT, no key, 1200 req/min)
      if (closes.length < 21) {
        try {
          var r2 = await ft('https://api.binance.com/api/v3/klines?symbol='+ticker+'USDT&interval=1d&limit=300');
          if (r2.ok) {
            var d2 = await r2.json();
            if (Array.isArray(d2) && d2.length >= 21) {
              closes = d2.map(function(k){return parseFloat(k[4]);}).filter(function(v){return !isNaN(v);});
              activeCls = 'Crypto';
            }
          }
        } catch(e) {}
      }
      // 3. Alpha Vantage — US/global stocks fallback
      if (closes.length < 21 && avKey) {
        try {
          var r3 = await ft('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+ticker+'&outputsize=full&apikey='+avKey, 15000);
          if (r3.ok) {
            var d3 = await r3.json();
            var ts = d3['Time Series (Daily)'];
            if (ts) closes = Object.entries(ts).sort(function(a,b){return a[0]>b[0]?1:-1;}).map(function(e){return parseFloat(e[1]['4. close']);}).filter(function(v){return !isNaN(v);});
          }
        } catch(e) { console.warn('AV add',ticker,e.message); }
      }
      btn.disabled = false;
      if (closes.length < 21) {
        status.textContent = '\\u2717 No data found for ' + ticker;
        setTimeout(function() { status.textContent = ''; }, 5000);
        return;
      }
      // Cache so page reload shows indicators immediately
      try { localStorage.setItem('pc_'+ticker, JSON.stringify({c:closes.slice(-400), ts:Date.now()})); } catch {}
      list.push({ ticker: ticker, name: ticker, cls: activeCls });
      saveCustomTickers(list);
      status.textContent = '\\u2713 ' + ticker + ' added!';
      setTimeout(function(){ location.reload(); }, 300);
    }"""

NEW_DOADD_ASYNC = """    async function doAdd() {
      var ticker = input.value.trim().toUpperCase().replace(/[^A-Z0-9.\\-]/g, '');
      if (!ticker) return;
      var list = getCustomTickers();
      if (list.find(function(t) { return t.ticker === ticker; })) {
        status.textContent = ticker + ' already added';
        setTimeout(function() { status.textContent = ''; }, 2000);
        return;
      }
      var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
      btn.disabled = true;
      status.textContent = 'Fetching ' + ticker + '...';
      var result = { closes: [], cls: null };
      try {
        if (window._fetchTicker) result = await window._fetchTicker(ticker);
      } catch(e) { console.warn('_fetchTicker', ticker, e.message); }
      btn.disabled = false;
      if (!result.closes || result.closes.length < 21) {
        status.textContent = '\\u2717 No data found for ' + ticker;
        setTimeout(function() { status.textContent = ''; }, 5000);
        return;
      }
      if (result.cls) activeCls = result.cls;
      try { localStorage.setItem('pc_'+ticker, JSON.stringify({c:result.closes.slice(-400), ts:Date.now()})); } catch {}
      list.push({ ticker: ticker, name: ticker, cls: activeCls });
      saveCustomTickers(list);
      status.textContent = '\\u2713 ' + ticker + ' added!';
      setTimeout(function(){ location.reload(); }, 300);
    }"""

if OLD_DOADD_ASYNC in content:
    content = content.replace(OLD_DOADD_ASYNC, NEW_DOADD_ASYNC, 1)
    changes += 1
    print('✓  Main doAdd() now delegates to window._fetchTicker')
elif 'await window._fetchTicker(ticker)' in content:
    print('–  doAdd() already delegates')
else:
    print('✗  async doAdd() not matched')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
