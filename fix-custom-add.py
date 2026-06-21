"""
fix-custom-add.py — Skip Yahoo search validation (CORS-blocked in many browsers).
Just add the ticker directly and let the data fetch validate it implicitly.
Run: python fix-custom-add.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

OLD_ADD = """      // Quick validate via Yahoo Finance search
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

NEW_ADD = """      // Add directly — data fetch will show NO DATA if ticker is invalid
      list.push({ ticker: ticker, name: ticker });
      saveCustomTickers(list);
      location.reload();"""

if OLD_ADD in content:
    content = content.replace(OLD_ADD, NEW_ADD, 1)
    changes += 1
    print('✓  Custom ticker add: removed CORS-blocked Yahoo validation, add directly')
elif 'Add directly' in content:
    print('–  Already using direct add')
else:
    print('✗  Old add block not matched')
    idx = content.find('Quick validate via Yahoo')
    if idx != -1: print(repr(content[idx:idx+200]))

if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
