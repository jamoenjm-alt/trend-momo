"""
fix-row-delete.py — Adds an X delete button to each row for user-added custom
tickers. Pre-defined tickers (hardcoded in WATCHLIST) get no X button.
The X removes the ticker from localStorage and reloads.
Run: python fix-row-delete.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. CSS for the delete button in rows ──────────────────────────────────────
DELETE_CSS = """
    /* ── Custom ticker row delete button ─────────────────────── */
    .ct-row-del {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      margin-left: 6px;
      background: none;
      border: 1px solid #475569;
      border-radius: 3px;
      color: #475569;
      font-size: 0.55rem;
      line-height: 1;
      cursor: pointer;
      vertical-align: middle;
      padding: 0;
      flex-shrink: 0;
    }
    .ct-row-del:hover { border-color: #ef4444; color: #ef4444; background: rgba(239,68,68,0.1); }"""

if '.ct-row-del {' not in content:
    content = content.replace('</style>', DELETE_CSS + '\n  </style>', 1)
    changes += 1
    print('✓  Row delete button CSS added')
else:
    print('–  Delete CSS already present')

# ── 2. Inject JS that adds X buttons to custom ticker rows after React renders ─
DELETE_JS = """
<script>
/* Add ✕ delete buttons to user-added custom ticker rows */
(function() {
  function getCustomTickers() {
    try { return JSON.parse(localStorage.getItem('customTickers') || '[]'); } catch { return []; }
  }
  function deleteTicker(ticker) {
    var list = getCustomTickers().filter(function(t) { return t.ticker !== ticker; });
    localStorage.setItem('customTickers', JSON.stringify(list));
    location.reload();
  }
  function addDeleteButtons() {
    var customTickers = getCustomTickers().map(function(t) { return t.ticker; });
    if (!customTickers.length) return;
    var rows = document.querySelectorAll('tr');
    rows.forEach(function(row) {
      var cells = row.querySelectorAll('td');
      if (!cells.length) return;
      var tickerCell = cells[0];
      var tickerText = tickerCell ? tickerCell.textContent.trim() : '';
      // Only add button if this row's ticker is a user-added one and button not already there
      if (customTickers.indexOf(tickerText) !== -1 && !row.querySelector('.ct-row-del')) {
        var btn = document.createElement('button');
        btn.className = 'ct-row-del';
        btn.title = 'Remove ' + tickerText;
        btn.textContent = '✕';
        btn.addEventListener('click', function(e) {
          e.stopPropagation();
          if (confirm('Remove ' + tickerText + '?')) deleteTicker(tickerText);
        });
        // Insert after the ticker text in the first cell
        tickerCell.appendChild(btn);
      }
    });
  }
  // Poll until rows are rendered
  var attempts = 0;
  var iv = setInterval(function() {
    attempts++;
    addDeleteButtons();
    if (attempts > 80) clearInterval(iv);
    // Keep re-running — React may re-render rows as data loads
  }, 200);
})();
</script>"""

if 'ct-row-del' not in content or 'Add ✕ delete buttons' not in content:
    content = content.replace('</body>', DELETE_JS + '\n</body>', 1)
    changes += 1
    print('✓  Row delete button JS injected')
else:
    print('–  Delete JS already present')

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
