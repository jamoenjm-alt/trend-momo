/* ============================================================================
 *  WATER - strategy backtest engine
 *  Cross-sectional momentum rotation with a breadth risk-off (cash) switch.
 *  Reads water-signals.js (the site's exact buyScore/computeSignals math,
 *  extracted by water.py) so the backtest can never drift from the live page.
 *
 *  Usage:  node water-backtest.js [history.json]
 *    history.json = { "AAPL":[closes...], ... }  (oldest first)
 *  Writes water-equity.json (equity curve) for the website chart.
 * ==========================================================================*/
const fs = require('fs'), path = require('path');
const dir = __dirname;
const { WATCHLIST, computeSignals, buyScore } = require(path.join(dir, 'water-signals.js'));

const PR = {
  REBAL:   +(process.env.REBAL   || 20),    // trading days between rebalances (~monthly)
  HOLD:    +(process.env.HOLD    || 20),
  TOPN:    +(process.env.TOPN    || 5),      // names held when risk-on
  FLOOR:   +(process.env.FLOOR   || 6),      // min buyScore to be eligible
  BREADTH: +(process.env.BREADTH || 0.35),   // < this fraction bullish -> all cash
  MINHIST: +(process.env.MINHIST || 63),     // bars of history before first trade
  MINBARS: +(process.env.MINBARS || 0),      // require >= this many bars to enter universe
};
const ALLOWED = new Set(['Watch', 'Top20', 'ASX', 'HK', 'Commodity', 'Index']);

function run(histPath) {
  const hist = JSON.parse(fs.readFileSync(histPath, 'utf8'));
  const uni = [...new Set(WATCHLIST
    .filter(w => ALLOWED.has(w.cls) && hist[w.ticker]
      && hist[w.ticker].length >= Math.max(PR.MINBARS, PR.MINHIST + PR.HOLD + 5))
    .map(w => w.ticker))];
  if (uni.length < PR.TOPN) throw new Error('universe too small: ' + uni.length);
  const L = Math.min(...uni.map(t => hist[t].length));   // common window (tail-aligned)
  const S = {}; uni.forEach(t => S[t] = hist[t].slice(-L));

  let eq = 1, bn = 1, pk = 1, dd = 0, cash = 0, per = 0, win = 0;
  const curve = [];
  for (let t = PR.MINHIST; t <= L - 1 - PR.HOLD; t += PR.REBAL) {
    const sc = uni.map(tk => {
      const s = computeSignals(S[tk].slice(0, t + 1));
      return { tk, score: s ? buyScore(s) : 0 };
    });
    const bullFrac = sc.filter(x => x.score >= 5).length / sc.length;
    let held = [];
    if (bullFrac >= PR.BREADTH) held = sc.filter(x => x.score >= PR.FLOOR).sort((a, b) => b.score - a.score).slice(0, PR.TOPN);
    let r = 0; for (const h of held) r += (S[h.tk][t + PR.HOLD] / S[h.tk][t] - 1); r /= PR.TOPN;
    if (!held.length) cash++;
    let br = 0; for (const tk of uni) br += (S[tk][t + PR.HOLD] / S[tk][t] - 1); br /= uni.length;
    eq *= (1 + r); bn *= (1 + br);
    pk = Math.max(pk, eq); dd = Math.min(dd, eq / pk - 1);
    per++; if (r > br) win++;
    curve.push({ i: t, equity: +eq.toFixed(4), bench: +bn.toFixed(4), cash: !held.length, held: held.map(h => h.tk) });
  }
  const y = L / 252, cagr = Math.pow(eq, 1 / y) - 1, bc = Math.pow(bn, 1 / y) - 1;
  return {
    universe: uni.length, bars: L, years: +y.toFixed(2), rebalances: per,
    totalReturnPct: +((eq - 1) * 100).toFixed(1), benchReturnPct: +((bn - 1) * 100).toFixed(1),
    cagrPct: +(cagr * 100).toFixed(1), benchCagrPct: +(bc * 100).toFixed(1),
    maxDrawdownPct: +(dd * 100).toFixed(1), pctTimeInCash: +(100 * cash / per).toFixed(0),
    beatBenchPctOfPeriods: +(100 * win / per).toFixed(0), curve,
  };
}

const out = run(process.argv[2] || path.join(dir, 'water-history.json'));
const { curve, ...stats } = out;
fs.writeFileSync(path.join(dir, 'water-equity.json'), JSON.stringify({ params: PR, stats, curve }));
console.log('WATER params:', JSON.stringify(PR));
console.log(JSON.stringify(stats, null, 2));
console.log('\nequity curve written -> water-equity.json (' + curve.length + ' points)');
