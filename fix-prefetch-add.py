"""
fix-prefetch-add.py — Rewrites the "Add Ticker" click handlers to:
1. Fetch data inline (TD → Binance → AV) BEFORE page reload
2. Cache result in localStorage
3. Only reload once data confirmed — ticker shows immediately with indicators
4. Show error if no data found (no blank rows)
Exposes API keys via window._KEYS so vanilla script can call APIs.
Run: python fix-prefetch-add.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Expose keys globally from the module ───────────────────────────────────
OLD_KEYS_LINE = "const AV_KEY_DEFAULT = 'M38DSB85MD33DQMB';"
NEW_KEYS_LINE = "const AV_KEY_DEFAULT = 'M38DSB85MD33DQMB';\n  window._KEYS={td:TD_KEY,av:AV_KEY_DEFAULT};"

if OLD_KEYS_LINE in content and 'window._KEYS' not in content:
    content = content.replace(OLD_KEYS_LINE, NEW_KEYS_LINE, 1)
    changes += 1
    print('✓  window._KEYS exposed from module')
elif 'window._KEYS' in content:
    print('–  window._KEYS already exposed')
else:
    print('✗  AV_KEY_DEFAULT line not matched')

# ── 2. Replace doAdd() in the main IIFE ──────────────────────────────────────
OLD_DOADD = """    function doAdd() {
      var ticker = input.value.trim().toUpperCase().replace(/[^A-Z0-9.]/g, '');
      if (!ticker) return;
      var list = getCustomTickers();
      if (list.find(function(t) { return t.ticker === ticker; })) {
        status.textContent = ticker + ' already added';
        setTimeout(function() { status.textContent = ''; }, 2000);
        return;
      }
      // Add directly — data fetch will show NO DATA if ticker is invalid
      var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
      list.push({ ticker: ticker, name: ticker, cls: activeCls });
      saveCustomTickers(list);
      location.reload();
    }"""

NEW_DOADD = """    async function doAdd() {
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
      // 1. Twelve Data — best for US + global stocks (800 credits/day, fresh since static prices bypass it)
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

if OLD_DOADD in content:
    content = content.replace(OLD_DOADD, NEW_DOADD, 1)
    changes += 1
    print('✓  Main doAdd() rewritten with async prefetch')
elif 'async function doAdd' in content:
    print('–  Main doAdd() already async')
else:
    print('✗  doAdd() not matched — check extract-add-functions.py output')

# ── 3. Replace backup go() ────────────────────────────────────────────────────
OLD_GO = """    function go() {
      var t = inp.value.trim().toUpperCase().replace(/[^A-Z0-9.]/g,'');
      if (!t) return;
      var list = [];
      try { list = JSON.parse(localStorage.getItem('customTickers')||'[]'); } catch{}
      if (list.some(function(x){return x.ticker===t;})) { inp.value=''; return; }
      var cls = (window._snavFilter && window._snavFilter!=='all') ? window._snavFilter : 'Custom';
      list.push({ticker:t, name:t, cls:cls});
      localStorage.setItem('customTickers', JSON.stringify(list));
      location.reload();
    }"""

NEW_GO = """    async function go() {
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

if OLD_GO in content:
    content = content.replace(OLD_GO, NEW_GO, 1)
    changes += 1
    print('✓  Backup go() rewritten with async prefetch')
elif 'async function go' in content:
    print('–  Backup go() already async')
else:
    print('✗  go() not matched')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
                                    