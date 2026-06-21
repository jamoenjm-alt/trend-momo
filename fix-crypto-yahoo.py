"""
fix-crypto-yahoo.py — Three fixes:
1. Yahoo Finance fallback for crypto tickers that get no data from CoinCap
2. Rename "Top 20 US" -> "US Assets" everywhere
3. Ensure Custom tickers use Yahoo Finance fallback (not just TD)
Run: python fix-crypto-yahoo.py  then: .\\git-push.bat
"""
import shutil, sys, re

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Add Yahoo Finance fallback for crypto after cryptoMap is built ─────────
OLD_CRYPTO_MAP = "const cryptoMap=Object.fromEntries(cryptoAssets.map((t,i)=>[t,cryptoFetches[i]||[]]));"

NEW_CRYPTO_MAP = """const cryptoMap=Object.fromEntries(cryptoAssets.map((t,i)=>[t,cryptoFetches[i]||[]]));
    // Yahoo Finance fallback for crypto tickers with no data from CoinCap/CoinGecko
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

if OLD_CRYPTO_MAP in content:
    content = content.replace(OLD_CRYPTO_MAP, NEW_CRYPTO_MAP, 1)
    changes += 1
    print('✓  Yahoo Finance crypto fallback added')
elif 'failedCrypto' in content:
    print('–  Crypto Yahoo fallback already present')
else:
    print('✗  cryptoMap line not matched')
    idx = content.find('cryptoMap=Object.from')
    if idx != -1: print(repr(content[idx:idx+120]))

# ── 2. Rename "Top 20 US" → "US Assets" in SECTIONS array ────────────────────
OLD_SECTION_LABEL = "{ label: 'Top 20 US',       cls: 'Top20'     },"
NEW_SECTION_LABEL = "{ label: 'US Assets',        cls: 'Top20'     },"

if OLD_SECTION_LABEL in content:
    content = content.replace(OLD_SECTION_LABEL, NEW_SECTION_LABEL)
    changes += 1
    print("✓  SECTIONS: 'Top 20 US' → 'US Assets'")
elif "label: 'US Assets'" in content:
    print("–  SECTIONS label already 'US Assets'")
else:
    # Try looser match
    idx = content.find("'Top 20 US'")
    if idx != -1:
        print(f'✗  SECTIONS label not matched exactly; found at {idx}:')
        print(repr(content[idx-10:idx+50]))
    else:
        print("✗  'Top 20 US' not found in SECTIONS")

# ── 3. Rename in section nav JS SECTION_MAP ───────────────────────────────────
OLD_NAV_MAP = "'Top 20 US': 'Top20'"
NEW_NAV_MAP = "'US Assets': 'Top20'"

if OLD_NAV_MAP in content:
    content = content.replace(OLD_NAV_MAP, NEW_NAV_MAP)
    changes += 1
    print("✓  Section nav SECTION_MAP: 'Top 20 US' → 'US Assets'")
elif NEW_NAV_MAP in content:
    print('–  Nav map already updated')
else:
    print('✗  Section nav SECTION_MAP not matched')

# ── 4. Rename in section nav button HTML ──────────────────────────────────────
OLD_NAV_BTN = '>Top 20 US</button>'
NEW_NAV_BTN = '>US Assets</button>'

if OLD_NAV_BTN in content:
    content = content.replace(OLD_NAV_BTN, NEW_NAV_BTN)
    changes += 1
    print("✓  Section nav button: 'Top 20 US' → 'US Assets'")
elif NEW_NAV_BTN in content:
    print('–  Nav button already updated')
else:
    print('✗  Section nav button not matched')

# ── 5. Ensure Custom tickers also fall through to Yahoo Finance if TD fails ───
# The loadAll builds tdResults from TD batch; if a Custom ticker isn't in TD results,
# it gets empty closes. Add Yahoo fetch for Custom tickers with no closes.
# Look for where ASX/HK fallback loop is - insert Custom Yahoo fallback before it.
OLD_ASX_FALLBACK = "for (const a of WATCHLIST.filter(a=>(a.cls==='ASX'||a.cls==='HK')&&!staticData[a.ticker]))"

CUSTOM_YF_FALLBACK = """// Yahoo Finance fallback for Custom tickers that TD didn't return
    const customFailed=WATCHLIST.filter(a=>a.cls==='Custom'&&!staticData[a.ticker]&&!(newData[dataKey(a)]?.closes));
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
    }
    """ + OLD_ASX_FALLBACK

if OLD_ASX_FALLBACK in content and 'customFailed' not in content:
    content = content.replace(OLD_ASX_FALLBACK, CUSTOM_YF_FALLBACK, 1)
    changes += 1
    print('✓  Yahoo Finance fallback for Custom tickers added')
elif 'customFailed' in content:
    print('–  Custom YF fallback already present')
else:
    print('✗  ASX fallback anchor not found')
    idx = content.find("cls==='ASX'")
    if idx != -1: print(repr(content[idx-30:idx+80]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
