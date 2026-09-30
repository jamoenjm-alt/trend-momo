# -*- coding: utf-8 -*-
# Add a section selector to the buy-by-hold panel: one panel, dropdown switches the
# universe (All / Watch / US / Crypto / ASX / HK / Commodity). horizonBuys gains a
# section filter; BtcSignalPage gains hzSection state + a <select>.
import io
F='regime-board.html'
src=io.open(F,encoding='utf-8').read()
def rep(old,new,label):
    global src
    n=src.count(old)
    assert n==1,'EXPECTED 1 for [%s] got %d'%(label,n)
    src=src.replace(old,new); print('ok:',label)

# 1) horizonBuys signature + section filter
rep(
"""function horizonBuys(data) {
  // Each horizon ranks the signal that won it out-of-sample (see""",
"""function horizonBuys(data, section) {
  // Each horizon ranks the signal that won it out-of-sample (see""",
"horizonBuys signature")
rep(
"""  for (const a of WATCHLIST) {
    if (a.cls === 'Forex' || a.cls === 'Index') continue;
    if (seen[a.ticker]) continue;
    const d = data[a.ticker + '__' + a.cls]; const closes = d && d.closes;
    if (!closes || closes.length < 260 || !d.sigs) continue;
    seen[a.ticker] = 1;
    const sg = d.sigs;
    const px = closes[closes.length - 1];""",
"""  for (const a of WATCHLIST) {
    if (a.cls === 'Forex' || a.cls === 'Index') continue;
    if (section && section !== 'All' && a.cls !== section) continue;
    if (seen[a.ticker]) continue;
    const d = data[a.ticker + '__' + a.cls]; const closes = d && d.closes;
    if (!closes || closes.length < 260 || !d.sigs) continue;
    seen[a.ticker] = 1;
    const sg = d.sigs;
    const px = closes[closes.length - 1];""",
"horizonBuys section filter")

# 2) section state in BtcSignalPage
rep(
"""function BtcSignalPage({ data }) {
  let closes = null;""",
"""function BtcSignalPage({ data }) {
  const [hzSection, setHzSection] = useState('All');
  let closes = null;""",
"hzSection state")

# 3) pass section to horizonBuys
rep(
"  const hbuys = horizonBuys(data);",
"  const hbuys = horizonBuys(data, hzSection);",
"hbuys call")

# 4) header with dropdown
rep(
"    h('h3', { className: 'plan-h', style: { marginTop: 4 } }, '\U0001F4C8 Best buy — by how long you’ll hold it'),",
"""    h('div', { className: 'hz-head' },
      h('h3', { className: 'plan-h', style: { margin: 0 } }, '\U0001F4C8 Best buy — by how long you’ll hold it'),
      h('select', { className: 'hz-sel', value: hzSection, onChange: function(e){ setHzSection(e.target.value); } },
        [['All','All markets'],['Watch','Watchlist'],['Top20','US Top 100'],['Crypto','Crypto'],['ASX','ASX 50'],['HK','Hong Kong 30'],['Commodity','Commodities']].map(function(o){ return h('option', { key: o[0], value: o[0] }, o[1]); })
      )
    ),""",
"header dropdown")

# 5) CSS for head + select
rep(
"  .hz-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(178px,1fr)); gap:11px; margin:4px 0; }",
"""  .hz-head { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:4px; }
  .hz-sel { background:#0f1420; color:#e6edf3; border:1px solid #22304a; border-radius:8px; padding:5px 10px; font-size:0.72rem; font-family:inherit; cursor:pointer; }
  .hz-sel:hover { border-color:#38bdf8; }
  .hz-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(178px,1fr)); gap:11px; margin:4px 0; }""",
"hz-head/hz-sel CSS")

io.open(F,'w',encoding='utf-8',newline='').write(src)
nuls=open(F,'rb').read().count(b'\x00')
print('bytes:',len(src.encode('utf-8')),'NULs:',nuls)
assert nuls==0
