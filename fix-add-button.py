"""
fix-add-button.py — Replaces the complex polling wireBar() with a simple
direct event attachment. Also injects a guaranteed-fire backup script.
Run: python fix-add-button.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── Replace the entire wireBar function with a simpler direct version ─────────
OLD_WIREBAR = """  function wireBar() {
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
      var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
      list.push({ ticker: ticker, name: ticker, cls: activeCls });
      saveCustomTickers(list);
      location.reload();
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
  }, 100);"""

NEW_WIREBAR = """  function doAdd() {
    var input = document.getElementById('custom-ticker-input');
    var status = document.getElementById('custom-ticker-status');
    if (!input) return;
    var ticker = input.value.trim().toUpperCase().replace(/[^A-Z0-9.]/g, '');
    if (!ticker) return;
    var list = getCustomTickers();
    if (list.find(function(t) { return t.ticker === ticker; })) {
      if (status) { status.textContent = ticker + ' already added'; setTimeout(function() { status.textContent = ''; }, 2000); }
      return;
    }
    var activeCls = (window._snavFilter && window._snavFilter !== 'all') ? window._snavFilter : 'Custom';
    list.push({ ticker: ticker, name: ticker, cls: activeCls });
    saveCustomTickers(list);
    location.reload();
  }

  function wireBar() {
    var btn = document.getElementById('custom-ticker-add');
    var input = document.getElementById('custom-ticker-input');
    if (!btn || !input || btn.dataset.wired) return false;
    btn.dataset.wired = '1';
    btn.addEventListener('click', doAdd);
    input.addEventListener('keydown', function(e) { if (e.key === 'Enter') doAdd(); });
    renderChips();
    return true;
  }

  var attempts = 0;
  var iv = setInterval(function() {
    attempts++;
    insertBar();
    wireBar();
    if (attempts > 80) clearInterval(iv);
  }, 100);"""

if OLD_WIREBAR in content:
    content = content.replace(OLD_WIREBAR, NEW_WIREBAR, 1)
    changes += 1
    print('✓  wireBar replaced with simpler direct approach')
elif 'btn.dataset.wired' in content:
    print('–  wireBar already simplified')
else:
    print('✗  wireBar block not matched')
    idx = content.find('function wireBar()')
    if idx != -1: print(repr(content[idx:idx+200]))

# ── Inject a guaranteed backup <script> right after the bar HTML ──────────────
# This fires on DOMContentLoaded and ensures the button always works
BACKUP_SCRIPT = """
<script>
/* Guaranteed backup: wire Add button after DOM ready */
(function() {
  function wireAddBtn() {
    var btn = document.getElementById('custom-ticker-add');
    var inp = document.getElementById('custom-ticker-input');
    if (!btn || !inp || btn.dataset.gwired) return;
    btn.dataset.gwired = '1';
    function go() {
      var t = inp.value.trim().toUpperCase().replace(/[^A-Z0-9.]/g,'');
      if (!t) return;
      var list = [];
      try { list = JSON.parse(localStorage.getItem('customTickers')||'[]'); } catch{}
      if (list.some(function(x){return x.ticker===t;})) { inp.value=''; return; }
      var cls = (window._snavFilter && window._snavFilter!=='all') ? window._snavFilter : 'Custom';
      list.push({ticker:t, name:t, cls:cls});
      localStorage.setItem('customTickers', JSON.stringify(list));
      location.reload();
    }
    btn.addEventListener('click', go);
    inp.addEventListener('keydown', function(e){ if(e.key==='Enter') go(); });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireAddBtn);
  } else {
    wireAddBtn();
  }
  // Also try after a short delay in case elements load late
  setTimeout(wireAddBtn, 500);
  setTimeout(wireAddBtn, 1500);
})();
</script>"""

if 'Guaranteed backup: wire Add button' not in content:
    # Insert right after the closing </script> of the main custom ticker script block
    # Find the end of the main custom ticker IIFE
    marker = '</script>'
    # Find the script block that contains 'custom-ticker-bar'
    idx = content.find('id="custom-ticker-bar"')
    if idx != -1:
        # Find the next </script> after this
        end_script = content.find('</script>', idx)
        if end_script != -1:
            insert_at = end_script + len('</script>')
            content = content[:insert_at] + BACKUP_SCRIPT + content[insert_at:]
            changes += 1
            print('✓  Backup Add button wiring script injected')
        else:
            print('✗  Could not find </script> after custom-ticker-bar')
    else:
        print('✗  custom-ticker-bar marker not found')
else:
    print('–  Backup script already present')

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
