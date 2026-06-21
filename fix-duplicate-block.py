"""
fix-duplicate-block.py — Removes the duplicate failedCrypto block that was
injected twice when fix-crypto-yahoo.py ran two times in a row.
Run: python fix-duplicate-block.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The duplicate: after the first injection, OLD_CRYPTO_MAP is still the
# first line of NEW_CRYPTO_MAP, so the second run matched and inserted again.
# Result: two consecutive failedCrypto blocks. Remove the first occurrence.

DUPE_BLOCK = """    // Yahoo Finance fallback for crypto tickers with no data from CoinCap/CoinGecko
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
    }"""

count = content.count(DUPE_BLOCK)
print(f'failedCrypto block appears {count}x in file')

if count >= 2:
    # Remove just the first occurrence, keep the second
    first = content.find(DUPE_BLOCK)
    content = content[:first] + content[first+len(DUPE_BLOCK):]
    print('✓  Removed duplicate failedCrypto block')
    # Verify
    count2 = content.count(DUPE_BLOCK)
    print(f'  Now appears {count2}x')
elif count == 1:
    print('–  Only one copy found, no duplicate to remove')
    sys.exit(0)
else:
    print('✗  Block not found at all — checking for any failedCrypto...')
    idx = content.find('failedCrypto')
    while idx != -1:
        print(f'  at {idx}: {repr(content[idx:idx+80])}')
        idx = content.find('failedCrypto', idx+1)
    sys.exit(1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print('\n✓  Fixed. index.html synced. Run: .\\git-push.bat')
