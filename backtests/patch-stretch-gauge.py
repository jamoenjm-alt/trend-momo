# -*- coding: utf-8 -*-
# Add the stretch gauge to the Signal-page buy cards. 4 exact replacements.
import io
F='regime-board.html'
src=io.open(F,encoding='utf-8').read()
def rep(old,new,label):
    global src
    n=src.count(old)
    assert n==1,'EXPECTED 1 for [%s] got %d'%(label,n)
    src=src.replace(old,new); print('ok:',label)

# 1) carry cls into the pick object
rep(
"      regime: scoreToRegime(sg.allInd).label, up: up, dist: dist, r126: r126, stable: stable });",
"      regime: scoreToRegime(sg.allInd).label, up: up, dist: dist, r126: r126, stable: stable, cls: a.cls });",
"cls into pick")

# 2) stretchMeta() helper before HORIZONS
rep(
"const HORIZONS = [",
"""function stretchMeta(ext, cls) {
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
}
const HORIZONS = [""",
"stretchMeta helper")

# 3) render the gauge in each card
rep(
"""        h('div', { className: 'hz-vs' }, c.edge),
        h('div', { className: 'hz-note' }, c.note)
      );
    })),""",
"""        h('div', { className: 'hz-vs' }, c.edge),
        h('div', { className: 'hz-note' }, c.note),
        (pk && pk.dist != null) ? (function(){ var m = stretchMeta(pk.dist, pk.cls);
          return h('div', { className: 'hz-stretch' },
            h('div', { className: 'hz-st-top' },
              h('span', { className: 'hz-st-lbl' }, 'stretch vs 200d line'),
              h('span', { className: 'hz-st-val hz-st-' + m.tc }, m.valtxt)
            ),
            h('div', { className: 'hz-st-bar' },
              h('div', { className: 'hz-st-seg hz-st-g' }),
              h('div', { className: 'hz-st-seg hz-st-a' }),
              h('div', { className: 'hz-st-seg hz-st-r' }),
              h('div', { className: 'hz-st-mark', style: { left: m.pos + '%' } })
            ),
            h('div', { className: 'hz-st-note' }, m.note)
          );
        })() : null
      );
    })),""",
"gauge render")

# 4) CSS
rep(
"""  .hz-caveat .hz-beat { color:#fbbf24; }
</style>""",
"""  .hz-caveat .hz-beat { color:#fbbf24; }
  /* stretch gauge */
  .hz-stretch { margin-top:10px; padding-top:10px; border-top:1px solid #1c2740; }
  .hz-st-top { display:flex; justify-content:space-between; align-items:baseline; gap:6px; }
  .hz-st-lbl { font-size:0.58rem; color:#8896a5; letter-spacing:0.03em; text-transform:uppercase; }
  .hz-st-val { font-size:0.64rem; font-weight:700; white-space:nowrap; }
  .hz-st-val.hz-st-g { color:#4ade80; }
  .hz-st-val.hz-st-a { color:#facc15; }
  .hz-st-val.hz-st-r { color:#f87171; }
  .hz-st-bar { position:relative; display:flex; height:7px; border-radius:5px; overflow:hidden; margin:7px 0 0; }
  .hz-st-seg { height:100%; }
  .hz-st-g { width:25%; background:#16a34a; }
  .hz-st-a { width:37.5%; background:#ca8a04; }
  .hz-st-r { width:37.5%; background:#dc2626; }
  .hz-st-mark { position:absolute; top:-2px; width:2px; height:11px; background:#fff; box-shadow:0 0 0 1px rgba(0,0,0,.55); transform:translateX(-1px); }
  .hz-st-note { font-size:0.6rem; color:#7b8794; line-height:1.42; margin-top:6px; }
</style>""",
"stretch CSS")

io.open(F,'w',encoding='utf-8',newline='').write(src)
nuls=open(F,'rb').read().count(b'\x00')
print('bytes:',len(src.encode('utf-8')),'NULs:',nuls)
assert nuls==0
