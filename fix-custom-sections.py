"""
fix-custom-sections.py — Makes the Add Ticker bar section-aware:
- While on "Crypto" tab → ticker stored as cls:'Crypto', fetched via CoinCap/Yahoo-USD
- While on "ASX" tab → cls:'ASX', Yahoo .AX suffix
- While on "US Assets" / "Watchlist" / other → cls:'Custom', TD/Yahoo fetch
- Pre-React injection uses stored cls so tickers appear in the right section
- Removes CORS-blocked Yahoo validation (add directly)
Run: python fix-custom-sections.py  then: .\\git-push.bat
"""
import shutil, sys, re

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Pre-React injection: use stored cls instead of hardcoded 'Custom' ──────
OLD_INJECT = "        WATCHLIST.push({ ticker: t.ticker, name: t.name || t.ticker, cls: 'Custom' });"
NEW_INJECT = "        WATCHLIST.push({ ticker: t.ticker, name: t.name || t.ticker, cls: t.cls || 'Custom' });"

if OLD_INJECT in content:
    content = content.replace(OLD_INJECT, NEW_INJECT, 1)
    changes += 1
    print('✓  Pre-React injection: uses stored cls instead of hardcoded Custom')
elif NEW_INJECT in content:
    print('–  Pre-React cls fix already applied')
else:
    print('✗  Pre-React injection line not matched')
    idx = content.find("WATCHLIST.push({ ticker: t.ticker")
    if idx != -1: print(repr(content[idx:idx+100]))

# ── 2. Custom YF fallback: also handle ASX tickers with .AX suffix ────────────
OLD_CUSTOM_YF = """    const customFailed=WATCHLIST.filter(a=>a.cls==='Custom'&&!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes));
    if(customFailed.length){
      await Promise.all(customFailed.map(async a=>{
        try{
          const sym=a.ticker.replace('.','-');
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
    }"""

NEW_CUSTOM_YF = """    // Yahoo Finance fallback for user-added tickers (Custom/ASX/Crypto cls) with no data
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

if OLD_CUSTOM_YF in content:
    content = content.replace(OLD_CUSTOM_YF, NEW_CUSTOM_YF, 1)
    changes += 1
    print('✓  Custom/ASX/Crypto YF fallbacks expanded')
elif 'cryptoCustomFailed' in content:
    print('–  Expanded fallback already present')
else:
    print('✗  Old custom YF fallback not matched')
    idx = content.find('customFailed=WATCHLIST')
    if idx != -1: print(repr(content[idx:idx+150]))

# ── 3. Replace the entire custom ticker bar script with section-aware version ──
OLD_SCRIPT_MARKER = '// Add directly — add the ticker directly and let the data fetch validate it implicitly'
# If fix-custom-add.py already ran, this comment exists. If not, look for old Yahoo search block.
if OLD_SCRIPT_MARKER not in content:
    OLD_SCRIPT_MARKER = '// Quick validate via Yahoo Finance search'

OLD_ADD_BLOCK_START = '      // Add directly — add the ticker directly and let the data fetch validate it implicitly\n      list.push({ ticker: ticker, name: ticker });\n      saveCustomTickers(list);\n      location.reload();'
# Also handle the case where fix-custom-add.py hasn't run yet
OLD_ADD_BLOCK_START_v2 = """      // Quick validate via Yahoo Finance search
      status.textContent = 'Checking ' + ticker + '...';
      fetch('https://query1.finance.yahoo.com/v1/finance/search?q=' + ticker + '&quotesCount=1&newsCount=0')
        .then(function(r) { return r.json(); })
        .then(function(d) {
          var quote = d.quotes && d.quotes[0];
          var name = (quote && (quote.shortname || quote.longname)) || ticker;
          list.push({ ticker: ticker, name: name });
          saveCustomTickers(list);
          status.textContent = '';
          location.reload();
        })
        .catch(function() {
          // Add anyway even if search fails
          list.push({ ticker: ticker, name: ticker });
          saveCustomTickers(list);
          status.textContent = '';
          location.reload();
        });"""

NEW_ADD_BLOCK = """      // Determine cls from active section filter
      var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
      list.push({ ticker: ticker, name: ticker, cls: activeCls });
      saveCustomTickers(list);
      location.reload();"""

applied = False
for old in [OLD_ADD_BLOCK_START, OLD_ADD_BLOCK_START_v2]:
    if old in content:
        content = content.replace(old, NEW_ADD_BLOCK, 1)
        changes += 1
        print('✓  Add block: now stores cls from active section filter')
        applied = True
        break
if not applied:
    if 'activeCls' in content:
        print('–  Section-aware add already applied')
    else:
        print('✗  Add block not matched')
        idx = content.find('doAdd')
        if idx != -1: print(repr(content[idx:idx+300]))

# ── 4. Update section nav to expose activeFilter globally ─────────────────────
# The section nav sets activeFilter locally. We need window._snavFilter so the
# custom ticker bar can read which section is active.
OLD_APPLY = "  function applyFilter(cls) {\n    activeFilter = cls;"
NEW_APPLY = "  function applyFilter(cls) {\n    activeFilter = cls;\n    window._snavFilter = cls;"

if OLD_APPLY in content:
    content = content.replace(OLD_APPLY, NEW_APPLY, 1)
    changes += 1
    print('✓  applyFilter: exposes active section via window._snavFilter')
elif 'window._snavFilter' in content:
    print('–  _snavFilter already exposed')
else:
    print('✗  applyFilter not matched')
    idx = content.find('function applyFilter')
    if idx != -1: print(repr(content[idx:idx+80]))

# ── 5. Update label on the bar to show current section ────────────────────────
# Replace static "+ Add Ticker" label with dynamic one (JS updates it)
OLD_LABEL = '<label>+ Add Ticker</label>'
NEW_LABEL = '<label id="custom-ticker-label">+ Add Ticker</label>'

if OLD_LABEL in content:
    content = content.replace(OLD_LABEL, NEW_LABEL, 1)
    changes += 1
    print('✓  Add Ticker label given id for dynamic updates')
elif 'custom-ticker-label' in content:
    print('–  Label id already present')
else:
    print('✗  Label not matched')

# ── 6. Wire label update into section nav button clicks ───────────────────────
# After applyFilter is called, update the label text
OLD_BTN_WIRE = """      btn.addEventListener('click', function() {
        applyFilter(btn.getAttribute('data-cls'));
      });"""
NEW_BTN_WIRE = """      btn.addEventListener('click', function() {
        applyFilter(btn.getAttribute('data-cls'));
        var lbl = document.getElementById('custom-ticker-label');
        var name = btn.textContent.trim();
        if (lbl) lbl.textContent = name === 'All' ? '+ Add Ticker' : '+ Add to ' + name;
      });"""

if OLD_BTN_WIRE in content:
    content = content.replace(OLD_BTN_WIRE, NEW_BTN_WIRE, 1)
    changes += 1
    print('✓  Section nav buttons update Add Ticker label on click')
elif 'Add to ' in content:
    print('–  Label update already wired')
else:
    print('✗  Button wire not matched')
    idx = content.find("btn.addEventListener('click'")
    if idx != -1: print(repr(content[idx:idx+120]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
