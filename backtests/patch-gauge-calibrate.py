# -*- coding: utf-8 -*-
# Recalibrate the stretch gauge: percentile scale from real distribution, separate
# for stocks vs crypto/commodity. Replaces stretchMeta() + widens the bar zones.
import io
F='regime-board.html'
src=io.open(F,encoding='utf-8').read()
def rep(old,new,label):
    global src
    n=src.count(old)
    assert n==1,'EXPECTED 1 for [%s] got %d'%(label,n)
    src=src.replace(old,new); print('ok:',label)

old_fn="""function stretchMeta(ext, cls) {
  // Maps distance above the 200d MA to a tier + base rate, from the 104k-obs
  // extension study (backtests/extension-study.md). Risk/expectation gauge, NOT
  // a sell signal — stretched names historically returned MORE.
  var pct = ext * 100;
  var pctl = ext >= 0.61 ? 'top ~1%' : ext >= 0.35 ? 'top ~5%' : ext >= 0.26 ? 'top ~10%' : ext >= 0.166 ? 'top ~25%' : 'normal range';
  var label, p10, dip;
  if (ext < 0.20)      { label = 'Normal';         p10 = '~1-in-5';  dip = 5; }
  else if (ext < 0.35) { label = 'Stretched';      p10 = '~1-in-3';  dip = 6; }
  else if (ext < 0.50) { label = 'Very stretched'; p10 = '~2-in-5';  dip = 8; }
  else if (ext < 0.80) { label = 'Extreme';        p10 = '~half';    dip = 9; }
  else                 { label = 'Extreme';        p10 = '~6-in-10'; dip = 13; }
  var tc  = ext < 0.20 ? 'g' : ext < 0.50 ? 'a' : 'r';
  var pos = Math.max(2, Math.min(98, (Math.min(ext, 0.80) / 0.80) * 100));
  var isEq = !(cls === 'Crypto' || cls === 'Commodity');
  var note = isEq
    ? label + ' — history: ' + p10 + ' see a 10%+ dip within 3 months. A stop tighter than ~' + dip + '% often gets shaken out here.'
    : label + ' — equity base rates; crypto/commodity dips run larger, so size smaller and give the stop more room.';
  var valtxt = (pct >= 0 ? '+' : '') + pct.toFixed(0) + '% vs 200d · ' + pctl;
  return { tc: tc, pos: pos, note: note, valtxt: valtxt };
}"""

new_fn="""function stretchMeta(ext, cls) {
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
rep(old_fn,new_fn,'stretchMeta percentile calibration')

# widen bar zones: green 0-75, amber 75-95, red 95-100 (match percentile tiers)
rep(
"""  .hz-st-g { width:25%; background:#16a34a; }
  .hz-st-a { width:37.5%; background:#ca8a04; }
  .hz-st-r { width:37.5%; background:#dc2626; }""",
"""  .hz-st-g { width:75%; background:#16a34a; }
  .hz-st-a { width:20%; background:#ca8a04; }
  .hz-st-r { width:5%;  background:#dc2626; }""",
"bar zone widths")

io.open(F,'w',encoding='utf-8',newline='').write(src)
nuls=open(F,'rb').read().count(b'\x00')
print('bytes:',len(src.encode('utf-8')),'NULs:',nuls)
assert nuls==0
