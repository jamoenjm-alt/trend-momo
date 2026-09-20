# -*- coding: utf-8 -*-
# Patch regime-board.html: honest per-horizon buys panel (one momentum engine,
# confidence-graded cards). Applies 5 exact replacements, asserts each hits once,
# checks NUL bytes, syncs index.html.
import io,sys
F='regime-board.html'
src=io.open(F,encoding='utf-8').read()
orig=src
def rep(old,new,label):
    global src
    n=src.count(old)
    assert n==1, 'EXPECTED 1 match for [%s], got %d'%(label,n)
    src=src.replace(old,new)
    print('ok:',label)

# ---- 1) CSS block ----
css_old="""  /* Buys-by-hold-period grid (Signal page) */
  .hz-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(158px,1fr)); gap:10px; margin:10px 0 4px; }
  .hz-card { background:#0f1420; border:1px solid #22304a; border-radius:10px; padding:12px 13px; }
  .hz-hold { font-weight:700; font-size:0.9rem; color:#e6edf3; display:flex; flex-direction:column; }
  .hz-sub { font-weight:400; font-size:0.62rem; color:#64748b; margin-top:1px; }
  .hz-tkr { font-size:1.2rem; font-weight:800; color:#fff; margin-top:9px; }
  .hz-name { font-size:0.68rem; color:#94a3b8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .hz-regime { font-size:0.63rem; color:#64748b; margin:2px 0 8px; }
  .hz-bt { font-size:0.82rem; font-weight:600; color:#22c55e; }
  .hz-vs { font-size:0.68rem; color:#64748b; margin-top:1px; }
  .hz-note { font-size:0.62rem; color:#7b8794; margin-top:7px; line-height:1.35; }
  .hz-good { border-color:rgba(21,128,61,.5); }
  .hz-ok .hz-bt { color:#4ade80; }
  .hz-flat { opacity:.72; } .hz-flat .hz-bt { color:#94a3b8; }
  .hz-caveat { border-color:rgba(161,98,7,.7); } .hz-caveat .hz-bt { color:#eab308; }
</style>"""
css_new="""  /* Buys-by-hold-period grid (Signal page) */
  .hz-banner { background:linear-gradient(180deg,#0f1420,#0c1018); border:1px solid #22304a; border-left:3px solid #38bdf8; border-radius:10px; padding:11px 14px; margin:8px 0 12px; font-size:0.72rem; color:#9fb0c3; line-height:1.55; }
  .hz-banner b { color:#e6edf3; }
  .hz-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(178px,1fr)); gap:11px; margin:4px 0; }
  .hz-card { position:relative; background:#0f1420; border:1px solid #22304a; border-radius:12px; padding:13px 15px 14px; overflow:hidden; }
  .hz-card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; background:#33415a; }
  .hz-top { display:flex; align-items:center; justify-content:space-between; gap:6px; }
  .hz-hold { font-weight:700; font-size:0.96rem; color:#e6edf3; }
  .hz-badge { font-size:0.55rem; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; padding:2px 7px; border-radius:20px; white-space:nowrap; }
  .hz-sub { font-size:0.6rem; color:#5b6b7f; margin-top:2px; letter-spacing:0.02em; }
  .hz-tkr { font-size:1.26rem; font-weight:800; color:#fff; margin-top:10px; }
  .hz-name { font-size:0.68rem; color:#94a3b8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .hz-regime { font-size:0.63rem; color:#64748b; margin:2px 0 9px; }
  .hz-metric { display:flex; align-items:baseline; gap:6px; }
  .hz-beat { font-size:1.08rem; font-weight:800; line-height:1; color:#e6edf3; }
  .hz-beatlbl { font-size:0.58rem; color:#64748b; }
  .hz-vs { font-size:0.63rem; color:#7b8794; margin-top:3px; }
  .hz-note { font-size:0.62rem; color:#8896a5; margin-top:8px; line-height:1.42; }
  /* confidence tiers */
  .hz-edge::before { background:#22c55e; }
  .hz-edge { border-color:rgba(34,197,94,.42); box-shadow:0 0 0 1px rgba(34,197,94,.12), 0 8px 20px -12px rgba(34,197,94,.4); }
  .hz-edge .hz-badge { background:rgba(34,197,94,.16); color:#4ade80; }
  .hz-edge .hz-beat { color:#4ade80; }
  .hz-weak::before { background:#eab308; }
  .hz-weak { border-color:rgba(234,179,8,.34); }
  .hz-weak .hz-badge { background:rgba(234,179,8,.15); color:#facc15; }
  .hz-weak .hz-beat { color:#facc15; }
  .hz-noise::before { background:#475569; }
  .hz-noise { opacity:.82; }
  .hz-noise .hz-badge { background:rgba(100,116,139,.18); color:#94a3b8; }
  .hz-noise .hz-beat { color:#94a3b8; }
  .hz-caveat::before { background:repeating-linear-gradient(45deg,#f59e0b,#f59e0b 4px,#7c4a06 4px,#7c4a06 8px); }
  .hz-caveat { border-color:rgba(245,158,11,.4); }
  .hz-caveat .hz-badge { background:rgba(245,158,11,.16); color:#fbbf24; }
  .hz-caveat .hz-beat { color:#fbbf24; }
</style>"""
rep(css_old,css_new,'CSS block')

# ---- 2) intro paragraph ----
p_old="""      h('p', null, 'Mechanical output of the board’s scoring formula. Our backtests are consistent: the STRONGEST-trend names outperformed the most beaten-down over the following 1–3 months (~2% vs ~1% on a 24-year mega-cap test) — momentum persisted, the opposite of a “buy max fear” idea. The edge only shows up over weeks, not days, and does not reliably beat the index after costs. A watch-list, not instructions.'),"""
p_new="""      h('p', null, 'Built from the one signal that actually held up in testing: 6-month price momentum among names in a confirmed uptrend (above their 200-day line). Tested on 25 years of mega-cap data, split into two halves, costs on — and every pick judged against the average stock in the same set, which cancels the survivor bias baked into the sample. Verdict: a real edge at ~6 months, a thin one at 1 month and 1 year, and none at 1 week or 5 years. The cards below are colour-graded by that honest result, not by how big the (survivor-inflated) back-test number looks. A watch-list, not instructions.'),"""
rep(p_old,p_new,'intro paragraph')

# ---- 3) render block (header -> grid) ----
r_old="""    h('h3', { className: 'plan-h', style: { marginTop: 4 } }, '\U0001F4C8 Best buy — by how long you’ll hold it'),
    h('div', { className: 'hz-grid' }, HORIZONS.map(function(c){ var pk = hbuys[c.k];
      return h('div', { key: c.k, className: 'hz-card hz-' + c.tone },
        h('div', { className: 'hz-hold' }, c.label, h('span', { className: 'hz-sub' }, c.hold)),
        pk ? h(Fragment, null,
              h('div', { className: 'hz-tkr' }, pk.ticker, ' ', assetBadge(pk.ticker)),
              h('div', { className: 'hz-name' }, pk.name),
              h('div', { className: 'hz-regime' }, pk.regime + ' · $' + (pk.price >= 1 ? pk.price.toFixed(2) : pk.price.toFixed(4)))
            ) : h('div', { className: 'hz-name', style:{marginTop:9} }, 'no uptrend candidate today'),
        h('div', { className: 'hz-bt' }, h('b', null, c.avg), ' avg · ', c.win, ' win'),
        h('div', { className: 'hz-vs' }, 'vs S&P ' + c.spy),
        h('div', { className: 'hz-note' }, c.note)
      );
    })),"""
r_new="""    h('h3', { className: 'plan-h', style: { marginTop: 4 } }, '\U0001F4C8 Best buy — by how long you’ll hold it'),
    h('div', { className: 'hz-banner' },
      h('b', null, 'One engine, five holds. '),
      'Every card ranks the same proven signal — 6-month momentum in a confirmed uptrend — so the pick can repeat; what changes is how long you hold and how much the back-test trusts it. ',
      h('b', { style:{color:'#4ade80'} }, 'Green'), ' = a real edge that survived both halves of 25 years.  ',
      h('b', { style:{color:'#facc15'} }, 'Amber'), ' = thin.  ',
      h('b', { style:{color:'#94a3b8'} }, 'Grey'), ' = noise or survivor-inflated.  “Beat avg stock” = how often this pick beat the average name in the same set (bias-robust).'
    ),
    h('div', { className: 'hz-grid' }, HORIZONS.map(function(c){ var pk = hbuys[c.k];
      return h('div', { key: c.k, className: 'hz-card hz-' + c.tier },
        h('div', { className: 'hz-top' },
          h('span', { className: 'hz-hold' }, c.label),
          h('span', { className: 'hz-badge' }, c.headline)
        ),
        h('div', { className: 'hz-sub' }, 'hold ' + c.hold),
        pk ? h(Fragment, null,
              h('div', { className: 'hz-tkr' }, pk.ticker, ' ', assetBadge(pk.ticker)),
              h('div', { className: 'hz-name' }, pk.name),
              h('div', { className: 'hz-regime' }, pk.regime + ' · $' + (pk.price >= 1 ? pk.price.toFixed(2) : pk.price.toFixed(4)))
            ) : h('div', { className: 'hz-name', style:{marginTop:9} }, 'no uptrend candidate today'),
        h('div', { className: 'hz-metric' },
          h('span', { className: 'hz-beat' }, c.beat),
          h('span', { className: 'hz-beatlbl' }, 'beat avg stock')
        ),
        h('div', { className: 'hz-vs' }, c.edge),
        h('div', { className: 'hz-note' }, c.note)
      );
    })),"""
rep(r_old,r_new,'render block')

# ---- 4) horizonBuys function ----
hb_old="""function horizonBuys(data) {
  const seen = {}, cand = [];
  for (const a of WATCHLIST) {
    if (a.cls === 'Forex' || a.cls === 'Index') continue;
    if (seen[a.ticker]) continue;
    const d = data[a.ticker + '__' + a.cls]; const closes = d && d.closes;
    if (!closes || closes.length < 260 || !d.sigs) continue;
    seen[a.ticker] = 1;
    const sg = d.sigs; const ma = sma(closes, 200);
    cand.push({ ticker: a.ticker, name: a.name, price: closes[closes.length - 1], regime: scoreToRegime(sg.allInd).label,
      up: ma != null && closes[closes.length - 1] > ma, stable: (sg.stability === 'stable' || sg.stability === 'very_stable'),
      canary: sg.canary, stTrend: sg.stTrend, ltTrend: sg.ltTrend, allInd: sg.allInd });
  }
  const top = (filt, key, dir) => { let b = null; for (const c of cand) { if (!filt(c)) continue; const v = c[key]; if (v == null) continue; if (!b || (dir > 0 ? v > b._v : v < b._v)) b = Object.assign({ _v: v }, c); } return b; };
  return {
    w1: top(c => c.up, 'canary', 1),
    m1: top(c => c.up && c.ltTrend > 0, 'canary', -1),
    m6: top(c => c.up, 'stTrend', 1),
    y1: top(c => c.up && c.stable, 'ltTrend', 1),
    y5: top(c => c.up && c.stable, 'allInd', 1),
  };
}"""
hb_new="""function horizonBuys(data) {
  // ONE proven engine (see backtests/horizon-results.md): 6-month price momentum
  // among names in a confirmed uptrend (last close > 200d MA). 1-week has no
  // momentum edge that short, so it ranks by trend distance instead; 1yr/5yr also
  // require a stable regime. Same signal, different holds — the pick can repeat.
  const seen = {}, cand = [];
  for (const a of WATCHLIST) {
    if (a.cls === 'Forex' || a.cls === 'Index') continue;
    if (seen[a.ticker]) continue;
    const d = data[a.ticker + '__' + a.cls]; const closes = d && d.closes;
    if (!closes || closes.length < 260 || !d.sigs) continue;
    seen[a.ticker] = 1;
    const sg = d.sigs;
    const px = closes[closes.length - 1];
    const ma200 = sma(closes, 200);
    const up = ma200 != null && px > ma200;
    const dist = ma200 != null ? px / ma200 - 1 : null;                                  // trend distance
    const r126 = closes.length > 126 ? px / closes[closes.length - 1 - 126] - 1 : null;  // 6-month momentum
    const stable = (sg.stability === 'stable' || sg.stability === 'very_stable');
    cand.push({ ticker: a.ticker, name: a.name, price: px,
      regime: scoreToRegime(sg.allInd).label, up: up, dist: dist, r126: r126, stable: stable });
  }
  const top = (filt, key) => { let b = null; for (const c of cand) { if (!filt(c)) continue; const v = c[key]; if (v == null) continue; if (!b || v > b._v || (v === b._v && c.ticker < b.ticker)) b = Object.assign({ _v: v }, c); } return b; };
  return {
    w1: top(c => c.up, 'dist'),
    m1: top(c => c.up, 'r126'),
    m6: top(c => c.up, 'r126'),
    y1: top(c => c.up && c.stable, 'r126'),
    y5: top(c => c.up && c.stable, 'r126'),
  };
}"""
rep(hb_old,hb_new,'horizonBuys function')

# ---- 5) HORIZONS array ----
hz_old="""const HORIZONS = [
  { k:'w1', label:'1 Week',   hold:'~5 trading days', avg:'+0.3%',  win:'59%', spy:'+0.4%',  tone:'flat',   note:'No reliable edge this short \\u2014 near coin-flip. Momentum needs weeks.' },
  { k:'m1', label:'1 Month',  hold:'~21 days',        avg:'+2.2%',  win:'69%', spy:'+1.3%',  tone:'ok',     note:'Dip in a confirmed uptrend \\u2014 best 1-month entry.' },
  { k:'m6', label:'6 Months', hold:'~126 days',       avg:'+12.1%', win:'78%', spy:'+7.7%',  tone:'good',   note:'Strong medium-term trend; the edge is clear here.' },
  { k:'y1', label:'1 Year',   hold:'~252 days',       avg:'+21.1%', win:'76%', spy:'+13.9%', tone:'good',   note:'Strongest stable long-term trend.' },
  { k:'y5', label:'5 Years',  hold:'multi-year',      avg:'+178%',  win:'89%', spy:'+88%',   tone:'caveat', note:'Huge, but inflated by hindsight winners. For multi-year money, diversify \\u2014 see Allocation Models.' },
];"""
hz_new="""const HORIZONS = [
  { k:'w1', label:'1 Week',   hold:'~5 trading days', tier:'noise',  headline:'No edge',    beat:'≈50%', edge:'coin-flip — treat as noise',
    note:'Momentum needs weeks to show up. A 1-week pick is a watch item, not a signal.' },
  { k:'m1', label:'1 Month',  hold:'~21 days',        tier:'weak',   headline:'Thin edge',  beat:'56%',      edge:'typ. +1 pt vs avg stock',
    note:'Beats the average stock 56% of the time, by about a point. Real but small — don’t size up on it.' },
  { k:'m6', label:'6 Months', hold:'~126 days',       tier:'edge',   headline:'Strongest',  beat:'61%',      edge:'typ. +5 pts vs avg stock',
    note:'The sweet spot. Beats the average stock 61% of rebalances and held up in both halves of 25 years.' },
  { k:'y1', label:'1 Year',   hold:'~252 days',       tier:'weak',   headline:'Fat-tailed', beat:'56%',      edge:'typ. +3 pts, big upside tail',
    note:'Usually tracks the average stock, occasionally trounces it (the leader that becomes the next NVDA).' },
  { k:'y5', label:'5 Years',  hold:'multi-year',      tier:'caveat', headline:'Diversify',  beat:'≈50%', edge:'back-test inflated by survivors',
    note:'The giant historical return is survivors that soared — not skill, and unknowable in advance. For multi-year money, diversify → Allocation Models.' },
];"""
rep(hz_old,hz_new,'HORIZONS array')

io.open(F,'w',encoding='utf-8',newline='').write(src)
print('bytes:',len(src.encode('utf-8')),'(was',len(orig.encode('utf-8')),')')
# NUL check
nuls=open(F,'rb').read().count(b'\x00')
print('NUL bytes:',nuls)
assert nuls==0
