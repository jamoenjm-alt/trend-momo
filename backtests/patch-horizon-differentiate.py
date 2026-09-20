# -*- coding: utf-8 -*-
# Differentiate the buy cards by horizon-appropriate, individually-validated signals
# (backtests/horizon-differentiate.py): distance(1wk) / 6-mo mom(1mo,6mo) /
# 12-mo mom(1yr) / froth-screened mom(5yr).
import io
F='regime-board.html'
src=io.open(F,encoding='utf-8').read()
def rep(old,new,label):
    global src
    n=src.count(old)
    assert n==1,'EXPECTED 1 for [%s] got %d'%(label,n)
    src=src.replace(old,new); print('ok:',label)

# 1) horizonBuys header comment
rep(
"""  // ONE proven engine (see backtests/horizon-results.md): 6-month price momentum
  // among names in a confirmed uptrend (last close > 200d MA). 1-week has no
  // momentum edge that short, so it ranks by trend distance instead; 1yr/5yr also
  // require a stable regime. Same signal, different holds — the pick can repeat.""",
"""  // Each horizon ranks the signal that won it out-of-sample (see
  // backtests/horizon-differentiate.py): trend distance (1wk), 6-month momentum
  // (1mo/6mo), 12-month momentum (1yr), froth-screened 6-month momentum (5yr) —
  // all among names above their 200d MA. Different signals => different names.""",
"horizonBuys comment")

# 2) add r252 momentum
rep(
"    const r126 = closes.length > 126 ? px / closes[closes.length - 1 - 126] - 1 : null;  // 6-month momentum",
"    const r126 = closes.length > 126 ? px / closes[closes.length - 1 - 126] - 1 : null;  // 6-month momentum\n    const r252 = closes.length > 252 ? px / closes[closes.length - 1 - 252] - 1 : null;  // 12-month momentum",
"r252 var")

# 3) carry r252 into the candidate
rep(
"      regime: scoreToRegime(sg.allInd).label, up: up, dist: dist, r126: r126, stable: stable, cls: a.cls });",
"      regime: scoreToRegime(sg.allInd).label, up: up, dist: dist, r126: r126, r252: r252, stable: stable, cls: a.cls });",
"r252 into cand")

# 4) differentiated return block
rep(
"""  return {
    w1: top(c => c.up, 'dist'),
    m1: top(c => c.up, 'r126'),
    m6: top(c => c.up, 'r126'),
    y1: top(c => c.up && c.stable, 'r126'),
    y5: top(c => c.up && c.stable, 'r126'),
  };
}""",
"""  var y5 = top(c => c.up && c.dist != null && c.dist <= 0.35, 'r126');  // froth screened out
  if (!y5) y5 = top(c => c.up, 'r126');
  return {
    w1: top(c => c.up, 'dist'),                        // trend distance
    m1: top(c => c.up, 'r126'),                        // 6-month momentum
    m6: top(c => c.up, 'r126'),                        // 6-month momentum
    y1: top(c => c.up && c.r252 != null, 'r252'),      // 12-month momentum
    y5: y5,                                            // froth-screened momentum
  };
}""",
"differentiated return")

# 5) intro paragraph
rep(
"""      h('p', null, 'Built from the one signal that actually held up in testing: 6-month price momentum among names in a confirmed uptrend (above their 200-day line). Tested on 25 years of mega-cap data, split into two halves, costs on — and every pick judged against the average stock in the same set, which cancels the survivor bias baked into the sample. Verdict: a real edge at ~6 months, a thin one at 1 month and 1 year, and none at 1 week or 5 years. The cards below are colour-graded by that honest result, not by how big the (survivor-inflated) back-test number looks. A watch-list, not instructions.'),""",
"""      h('p', null, 'Each hold uses the signal that actually won it in testing (25 years, split in two halves, costs on, every pick judged against the average stock to cancel survivor bias): trend distance for a week, 6-month momentum in the 1–6 month middle, 12-month momentum at a year, and froth-screened momentum for 5 years — so short and long horizons surface different names, not the same one five times. Cards are colour-graded by how real that edge was, not by the (survivor-inflated) back-test number. A watch-list, not instructions.'),""",
"intro paragraph")

# 6) banner
rep(
"""      h('b', null, 'One engine, five holds. '),
      'Every card ranks the same proven signal — 6-month momentum in a confirmed uptrend — so the pick can repeat; what changes is how long you hold and how much the back-test trusts it. ',
      h('b', { style:{color:'#4ade80'} }, 'Green'), ' = a real edge that survived both halves of 25 years.  ',
      h('b', { style:{color:'#facc15'} }, 'Amber'), ' = thin.  ',
      h('b', { style:{color:'#94a3b8'} }, 'Grey'), ' = noise or survivor-inflated.  “Beat avg stock” = how often this pick beat the average name in the same set (bias-robust).'""",
"""      h('b', null, 'Five holds, matched signals. '),
      'Each card uses the signal that won its horizon in testing — trend distance for a week, 6-month momentum in the middle, 12-month momentum at a year, froth-screened momentum for 5 years — so the names differ by horizon (1mo and 6mo share the 6-month signal, so those two can match). ',
      h('b', { style:{color:'#4ade80'} }, 'Green'), ' = beat the average stock in both halves of 25 years.  ',
      h('b', { style:{color:'#facc15'} }, 'Amber'), ' = thin.  ',
      h('b', { style:{color:'#94a3b8'} }, 'Grey'), ' = noise or survivor-inflated.  “Beat avg stock” = how often this pick beat the average name in the same set (bias-robust).'""",
"banner")

# 7) HORIZONS array with sig field + updated 1yr/5yr
rep(
"""const HORIZONS = [
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
];""",
"""const HORIZONS = [
  { k:'w1', label:'1 Week',   hold:'~5 trading days', sig:'trend distance',   tier:'noise',  headline:'No edge',    beat:'≈50%', edge:'coin-flip — treat as noise',
    note:'Hottest name vs its 200-day line — but 1-week moves are noise. A watch item, not a signal.' },
  { k:'m1', label:'1 Month',  hold:'~21 days',        sig:'6-month momentum', tier:'weak',   headline:'Thin edge',  beat:'56%',      edge:'typ. +1 pt vs avg stock',
    note:'6-month momentum. Beats the average stock 56% of the time, by about a point — real but small.' },
  { k:'m6', label:'6 Months', hold:'~126 days',       sig:'6-month momentum', tier:'edge',   headline:'Strongest',  beat:'61%',      edge:'typ. +5 pts vs avg stock',
    note:'6-month momentum — the sweet spot. Beats the average stock 61% of rebalances, both halves of 25 years.' },
  { k:'y1', label:'1 Year',   hold:'~252 days',       sig:'12-month momentum',tier:'edge',   headline:'Real edge',  beat:'62%',      edge:'a steadier leader than 6-mo',
    note:'12-month momentum — a different, more established leader than the 6-month pick. Beat the average stock 62% in both halves.' },
  { k:'y5', label:'5 Years',  hold:'multi-year',      sig:'momentum, froth screened', tier:'caveat', headline:'Diversify',  beat:'~57%', edge:'survivor-inflated',
    note:'Strong trend with the most-stretched name screened out. Any 5-yr single-name edge is mostly survivorship — diversify → Allocation Models.' },
];""",
"HORIZONS array")

# 8) show the signal on each card sub-line
rep(
"        h('div', { className: 'hz-sub' }, 'hold ' + c.hold),",
"        h('div', { className: 'hz-sub' }, 'hold ' + c.hold + ' · ' + c.sig),",
"card sub sig")

io.open(F,'w',encoding='utf-8',newline='').write(src)
nuls=open(F,'rb').read().count(b'\x00')
print('bytes:',len(src.encode('utf-8')),'NULs:',nuls)
assert nuls==0
