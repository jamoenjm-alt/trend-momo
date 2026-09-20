# -*- coding: utf-8 -*-
# Gauge v3: cross-sectional percentile vs the CURRENT board (by asset class),
# computed live; historical curve kept as fallback when a class has <20 names.
import io
F='regime-board.html'
src=io.open(F,encoding='utf-8').read()
def rep(old,new,label):
    global src
    n=src.count(old)
    assert n==1,'EXPECTED 1 for [%s] got %d'%(label,n)
    src=src.replace(old,new); print('ok:',label)

# 1) compute the board extension distribution alongside hbuys
rep(
"  const hbuys = horizonBuys(data);",
"  const hbuys = horizonBuys(data);\n  const extDist = boardExtensions(data);",
"extDist in render")

# 2) pass extDist into stretchMeta
rep(
"(function(){ var m = stretchMeta(pk.dist, pk.cls);",
"(function(){ var m = stretchMeta(pk.dist, pk.cls, extDist);",
"stretchMeta call arg")

# 3) replace stretchMeta with cross-sectional version + add boardExtensions
old_fn="""function stretchMeta(ext, cls) {
  // Percentile gauge calibrated to the REAL distribution of price-vs-200d-MA
  // extension (backtests/extension-calibrate.py): separate curves for volatile
  // assets (crypto/commodity) vs stocks, so nothing pins at an arbitrary cap.
  // Marker position = percentile of this reading within that asset class's
  // history. Risk/turbulence gauge, NOT a sell signal.
  var isVol = (cls === 'Crypto' || cls === 'Commodity');
  var bp = isVol
    ? [[5,0.036],[25,0.168],[50,0.313],[75,0.575],[90,1.178],[95,1.596],[99,2.174],[99.9,3.529]]
    : [[5,0.011],[25,0.049],[50,0.097],[75,0.167],[90,0.262],[95,0.352],[99,0.621],[99.9,1.36]];
  var pctl;
  if (ext <= bp[0][1]) { pctl = Math.max(0, bp[0][0] * (ext / bp[0][1])); }
  else {
    pctl = 100;
    for (var i = 1; i < bp.length; i++) {
      if (ext <= bp[i][1]) { var f = (ext - bp[i-1][1]) / (bp[i][1] - bp[i-1][1]); pctl = bp[i-1][0] + f * (bp[i][0] - bp[i-1][0]); break; }
    }
  }
  if (pctl > 100) pctl = 100;
  var tc  = pctl < 75 ? 'g' : pctl < 95 ? 'a' : 'r';
  var pos = Math.max(2, Math.min(98, pctl));
  var pctlLbl = pctl >= 99 ? 'top 1%' : pctl >= 95 ? 'top 5%' : pctl >= 90 ? 'top 10%' : pctl >= 75 ? 'top 25%' : 'normal range';
  var kind = isVol ? 'crypto' : 'stocks';
  var pctv = ext * 100;
  var valtxt = (pctv >= 0 ? '+' : '') + pctv.toFixed(0) + '% vs 200d · ' + pctlLbl + ' for ' + kind;
  var note;
  if (isVol) {
    note = 'Stretched even for crypto (' + pctlLbl + ') — swings are violent: 10%+ dips are the norm and 20%+ common within 3 months. Size small, use wide stops.';
  } else {
    var p10, dip;
    if (ext < 0.20)      { p10 = '~1-in-5';  dip = 5; }
    else if (ext < 0.35) { p10 = '~1-in-3';  dip = 6; }
    else if (ext < 0.50) { p10 = '~2-in-5';  dip = 8; }
    else if (ext < 0.80) { p10 = '~half';    dip = 9; }
    else                 { p10 = '~6-in-10'; dip = 13; }
    note = 'History at this stretch: ' + p10 + ' see a 10%+ dip within 3 months (typical dip ~' + dip + '%). A stop tighter than that often gets shaken out.';
  }
  return { tc: tc, pos: pos, note: note, valtxt: valtxt };
}"""

new_fn="""function boardExtensions(data) {
  // Current price-vs-200d-MA extension for every board name, split by asset class,
  // so the stretch gauge can rank a pick against the live board (see the top-of-board
  // calibration in backtests/extension-calibrate.py). Recomputed each render.
  var seen = {}, eq = [], cx = [];
  for (const a of WATCHLIST) {
    if (a.cls === 'Forex' || a.cls === 'Index') continue;
    if (seen[a.ticker]) continue; seen[a.ticker] = 1;
    const d = data[a.ticker + '__' + a.cls]; const closes = d && d.closes;
    if (!closes || closes.length < 200) continue;
    const ma = sma(closes, 200); if (ma == null || ma <= 0) continue;
    const e = closes[closes.length - 1] / ma - 1;
    if (a.cls === 'Crypto' || a.cls === 'Commodity') cx.push(e); else eq.push(e);
  }
  eq.sort(function(x, y){ return x - y; });
  cx.sort(function(x, y){ return x - y; });
  return { eq: eq, cx: cx };
}
function stretchMeta(ext, cls, dist) {
  // Cross-sectional gauge: how stretched this pick is vs the CURRENT board, by asset
  // class. Recalibrates live each day; historical curve is the fallback for a thin
  // class. Turbulence/risk gauge, NOT a sell signal.
  var isVol = (cls === 'Crypto' || cls === 'Commodity');
  var arr = dist ? (isVol ? dist.cx : dist.eq) : null;
  var pctl, live = false;
  if (arr && arr.length >= 20) {
    var below = 0; for (var j = 0; j < arr.length; j++) { if (arr[j] < ext) below++; }
    pctl = below / arr.length * 100; live = true;
  } else {
    var bp = isVol
      ? [[5,0.036],[25,0.168],[50,0.313],[75,0.575],[90,1.178],[95,1.596],[99,2.174],[99.9,3.529]]
      : [[5,0.011],[25,0.049],[50,0.097],[75,0.167],[90,0.262],[95,0.352],[99,0.621],[99.9,1.36]];
    if (ext <= bp[0][1]) { pctl = Math.max(0, bp[0][0] * (ext / bp[0][1])); }
    else { pctl = 100; for (var i = 1; i < bp.length; i++) { if (ext <= bp[i][1]) { var f = (ext - bp[i-1][1]) / (bp[i][1] - bp[i-1][1]); pctl = bp[i-1][0] + f * (bp[i][0] - bp[i-1][0]); break; } } }
  }
  if (pctl > 100) pctl = 100; if (pctl < 0) pctl = 0;
  var tc  = pctl < 75 ? 'g' : pctl < 95 ? 'a' : 'r';
  var pos = Math.max(2, Math.min(98, pctl));
  var pctlLbl = pctl >= 99 ? 'top 1%' : pctl >= 95 ? 'top 5%' : pctl >= 90 ? 'top 10%' : pctl >= 75 ? 'top 25%' : 'middle of the pack';
  var kind = isVol ? 'crypto you track' : 'stocks you track';
  var pctv = ext * 100;
  var valtxt = (pctv >= 0 ? '+' : '') + pctv.toFixed(0) + '% vs 200d · ' + pctlLbl + (live ? ' of ' + kind : ' (hist.)');
  var note;
  if (isVol) {
    note = 'Hotter than most crypto on the board — swings are violent: 10%+ dips are the norm and 20%+ common within 3 months. Size small, use wide stops.';
  } else {
    var p10, dip;
    if (ext < 0.20)      { p10 = '~1-in-5';  dip = 5; }
    else if (ext < 0.35) { p10 = '~1-in-3';  dip = 6; }
    else if (ext < 0.50) { p10 = '~2-in-5';  dip = 8; }
    else if (ext < 0.80) { p10 = '~half';    dip = 9; }
    else                 { p10 = '~6-in-10'; dip = 13; }
    note = 'History at this stretch: ' + p10 + ' see a 10%+ dip within 3 months (typical dip ~' + dip + '%). A stop tighter than that often gets shaken out.';
  }
  return { tc: tc, pos: pos, note: note, valtxt: valtxt };
}"""
rep(old_fn,new_fn,"cross-sectional stretchMeta + boardExtensions")

io.open(F,'w',encoding='utf-8',newline='').write(src)
nuls=open(F,'rb').read().count(b'\x00')
print('bytes:',len(src.encode('utf-8')),'NULs:',nuls)
assert nuls==0
