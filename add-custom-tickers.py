"""
add-custom-tickers.py — Adds "My Tickers" section with add/remove UI
Users type any ticker, hit Add, it fetches + shows with full indicators.
Persists in localStorage. Run: python add-custom-tickers.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. CSS for the custom ticker search bar ───────────────────────────────────
CUSTOM_CSS = """
    /* ── My Tickers search bar ─────────────────────────────── */
    #custom-ticker-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      background: #0f172a;
      border-bottom: 1px solid #1e293b;
    }
    #custom-ticker-bar label {
      font-size: 0.68rem;
      font-weight: 700;
      color: #64748b;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    #custom-ticker-input {
      background: #1e293b;
      border: 1px solid #334155;
      color: #e2e8f0;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 6px;
      width: 110px;
      text-transform: uppercase;
      outline: none;
    }
    #custom-ticker-input:focus { border-color: #3b82f6; }
    #custom-ticker-input::placeholder { color: #475569; text-transform: none; font-weight: 400; }
    #custom-ticker-add {
      background: #1d4ed8;
      border: none;
      color: #fff;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 5px 12px;
      border-radius: 6px;
      cursor: pointer;
      letter-spacing: 0.04em;
    }
    #custom-ticker-add:hover { background: #2563eb; }
    #custom-ticker-chips { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
    .ct-chip {
      display: flex;
      align-items: center;
      gap: 5px;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 5px;
      padding: 3px 8px;
      font-size: 0.68rem;
      font-weight: 700;
      color: #93c5fd;
    }
    .ct-chip button {
      background: none;
      border: none;
      color: #475569;
      cursor: pointer;
      font-size: 0.7rem;
      padding: 0;
      line-height: 1;
    }
    .ct-chip button:hover { color: #ef4444; }
    #custom-ticker-status { font-size: 0.68rem; color: #64748b; white-space: nowrap; }"""

if '#custom-ticker-bar {' not in content:
    content = content.replace('</style>', CUSTOM_CSS + '\n  </style>', 1)
    changes += 1
    print('✓  Custom ticker CSS added')
else:
    print('–  Custom ticker CSS already present')

# ── 2. Pre-React: inject custom tickers from localStorage into WATCHLIST ──────
# Place this right before the SECTIONS const so it runs before React mounts
OLD_SECTIONS_LINE = "const SECTIONS = ["
PRE_REACT_INJECT = """// ── Custom tickers from localStorage ──────────────────────────────────
(function() {
  try {
    var ct = JSON.parse(localStorage.getItem('customTickers') || '[]');
    ct.forEach(function(t) {
      if (!WATCHLIST.find(function(a) { return a.ticker === t.ticker; })) {
        WATCHLIST.push({ ticker: t.ticker, name: t.name || t.ticker, cls: 'Custom' });
      }
    });
  } catch(e) {}
})();

"""

if 'customTickers' not in content:
    if OLD_SECTIONS_LINE in content:
        content = content.replace(OLD_SECTIONS_LINE, PRE_REACT_INJECT + OLD_SECTIONS_LINE, 1)
        changes += 1
        print('✓  Pre-React custom ticker injection added')
    else:
        print('✗  SECTIONS const not found')
else:
    print('–  Custom ticker injection already present')

# ── 3. Add Custom section to SECTIONS array ───────────────────────────────────
OLD_SECTIONS_BLOCK = """const SECTIONS = [
  { label: 'Watchlist',       cls: 'Watch'     },"""
NEW_SECTIONS_BLOCK = """const SECTIONS = [
  { label: 'My Tickers',      cls: 'Custom'    },
  { label: 'Watchlist',       cls: 'Watch'     },"""

if OLD_SECTIONS_BLOCK in content and "cls: 'Custom'" not in content:
    content = content.replace(OLD_SECTIONS_BLOCK, NEW_SECTIONS_BLOCK, 1)
    changes += 1
    print("✓  'My Tickers' section added to SECTIONS")
elif "cls: 'Custom'" in content:
    print('–  Custom section already in SECTIONS')
else:
    print('✗  SECTIONS block not matched')

# ── 4. Add Custom cls to Twelve Data fetch ────────────────────────────────────
OLD_TD_FILTER = "['Watch','Top20','Commodity','Index'].includes(a.cls)"
NEW_TD_FILTER = "['Watch','Top20','Commodity','Index','Custom'].includes(a.cls)"

if OLD_TD_FILTER in content:
    content = content.replace(OLD_TD_FILTER, NEW_TD_FILTER)  # replace all occurrences
    changes += 1
    print('✓  Custom cls added to Twelve Data fetch path')
elif NEW_TD_FILTER in content:
    print('–  Custom cls already in TD fetch')
else:
    print('✗  TD filter not matched')

# ── 5. Inject the search bar UI + wiring JS before </body> ───────────────────
CUSTOM_UI = """
<div id="custom-ticker-bar">
  <label>+ Add Ticker</label>
  <input id="custom-ticker-input" type="text" placeholder="e.g. PLTR" maxlength="10" />
  <button id="custom-ticker-add">Add</button>
  <div id="custom-ticker-chips"></div>
  <span id="custom-ticker-status"></span>
</div>

<script>
(function() {
  function getCustomTickers() {
    try { return JSON.parse(localStorage.getItem('customTickers') || '[]'); } catch { return []; }
  }
  function saveCustomTickers(list) {
    localStorage.setItem('customTickers', JSON.stringify(list));
  }
  function removeTicker(ticker) {
    var list = getCustomTickers().filter(function(t) { return t.ticker !== ticker; });
    saveCustomTickers(list);
    location.reload();
  }
  function renderChips() {
    var container = document.getElementById('custom-ticker-chips');
    if (!container) return;
    var list = getCustomTickers();
    container.innerHTML = '';
    list.forEach(function(t) {
      var chip = document.createElement('div');
      chip.className = 'ct-chip';
      chip.innerHTML = '<span>' + t.ticker + '</span><button title="Remove" onclick="(function(){var l=JSON.parse(localStorage.getItem(\'customTickers\')||\'[]\').filter(function(x){return x.ticker!==\'' + t.ticker + '\'});localStorage.setItem(\'customTickers\',JSON.stringify(l));location.reload();})()">✕</button>';
      container.appendChild(chip);
    });
  }

  function insertBar() {
    var sectionNav = document.getElementById('section-nav');
    var bar = document.getElementById('custom-ticker-bar');
    if (!bar) return false;
    if (sectionNav && sectionNav.parentNode && !bar._inserted) {
      sectionNav.parentNode.insertBefore(bar, sectionNav.nextSibling);
      bar._inserted = true;
    }
    return true;
  }

  function wireBar() {
    var btn = document.getElementById('custom-ticker-add');
    var input = document.getElementById('custom-ticker-input');
    var status = document.getElementById('custom-ticker-status');
    if (!btn || !input || btn._wired) return false;
    btn._wired = true;

    function doAdd() {
      var ticker = input.value.trim().toUpperCase().replace(/[^A-Z0-9.]/g, '');
      if (!ticker) return;
      var list = getCustomTickers();
      if (list.find(function(t) { return t.ticker === ticker; })) {
        status.textContent = ticker + ' already added';
        setTimeout(function() { status.textContent = ''; }, 2000);
        return;
      }
      // Quick validate via Yahoo Finance search
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
        });
    }

    btn.addEventListener('click', doAdd);
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') doAdd();
    });
    renderChips();
    return true;
  }

  var attempts = 0;
  var iv = setInterval(function() {
    attempts++;
    insertBar();
    if (wireBar() || attempts > 60) clearInterval(iv);
  }, 100);
})();
</script>"""

if 'custom-ticker-bar' not in content or 'id="custom-ticker-bar"' not in content:
    content = content.replace('</body>', CUSTOM_UI + '\n</body>', 1)
    changes += 1
    print('✓  Custom ticker search bar UI injected')
else:
    print('–  Custom ticker UI already present')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
