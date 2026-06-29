/* WATER diagnosis sweep — runs principled variations against buy-and-hold.
 * Reads water-history.json + water-signals.js (no network). Usage: node water-sweep.js */
const fs = require('fs'), path = require('path');
const dir = __dirname;
const { WATCHLIST, computeSignals, buyScore } = require(path.join(dir, 'water-signals.js'));
const ALLOWED = new Set(['Watch', 'Top20', 'ASX', 'HK', 'Commodity', 'Index']);
const hist = JSON.parse(fs.readFileSync(process.argv[2] || path.join(dir, 'water-history.json'), 'utf8'));

function run(p) {
  const uni = [...new Set(WATCHLIST
    .filter(w => ALLOWED.has(w.cls) && hist[w.ticker] && hist[w.ticker].length >= Math.max(p.MINBARS, p.MINHIST + p.HOLD + 5))
    .map(w => w.ticker))];
  const L = Math.min(...uni.map(t => hist[t].length));
  const S = {}; uni.forEach(t => S[t] = hist[t].slice(-L));
  let eq = 1, bn = 1, pk = 1, dd = 0, bpk = 1, bdd = 0, cash = 0, per = 0, win = 0;
  for (let t = p.MINHIST; t <= L - 1 - p.HOLD; t += p.REBAL) {
    const sc = uni.map(tk => { const s = computeSignals(S[tk].slice(0, t + 1)); return { tk, score: s ? buyScore(s) : 0 }; });
    const bull = sc.filter(x => x.score >= 5).length / sc.length;
    let held = [];
    if (bull >= p.BREADTH) held = sc.filter(x => x.score >= p.FLOOR).sort((a, b) => b.score - a.score).slice(0, p.TOPN);
    let r = 0; for (const h of held) r += (S[h.tk][t + p.HOLD] / S[h.tk][t] - 1); r /= p.TOPN;
    if (!held.length) cash++;
    let br = 0; for (const tk of uni) br += (S[tk][t + p.HOLD] / S[tk][t] - 1); br /= uni.length;
    eq *= (1 + r); bn *= (1 + br);
    pk = Math.max(pk, eq); dd = Math.min(dd, eq / pk - 1);
    bpk = Math.max(bpk, bn); bdd = Math.min(bdd, bn / bpk - 1);
    per++; if (r > br) win++;
  }
  const y = L / 252;
  return { y, ret: (eq - 1) * 100, cagr: (Math.pow(eq, 1 / y) - 1) * 100, dd: dd * 100,
           bRet: (bn - 1) * 100, bCagr: (Math.pow(bn, 1 / y) - 1) * 100, bDD: bdd * 100,
           cashPct: 100 * cash / per, beat: 100 * win / per, uni: uni.length };
}
const base = { REBAL: 20, HOLD: 20, TOPN: 5, FLOOR: 6, BREADTH: 0.35, MINHIST: 63, MINBARS: 2400 };
const C = (o) => Object.assign({}, base, o);
const configs = [
  ['Water (default)',            C({})],
  ['No cash switch (always in)', C({ BREADTH: 0 })],
  ['Top 3',                      C({ TOPN: 3 })],
  ['Top 8',                     C({ TOPN: 8 })],
  ['Top 10',                    C({ TOPN: 10 })],
  ['Top 10, no cash',           C({ TOPN: 10, BREADTH: 0 })],
  ['Quarterly (REBAL/HOLD 60)',  C({ REBAL: 60, HOLD: 60 })],
  ['Stricter floor 7',          C({ FLOOR: 7 })],
  ['Looser cash (BREADTH .5)',   C({ BREADTH: 0.5 })],
];
const r0 = run(base);
console.log(`Window ${r0.y.toFixed(1)}y | universe ${r0.uni} | BUY-AND-HOLD (equal weight): ${r0.bRet.toFixed(0)}% total, ${r0.bCagr.toFixed(1)}% CAGR, ${r0.bDD.toFixed(0)}% maxDD\n`);
console.log('config'.padEnd(28), 'CAGR'.padStart(7), 'total'.padStart(8), 'maxDD'.padStart(7), 'cash%'.padStart(6), 'beatBH%'.padStart(8), '  vs B&H CAGR');
for (const [name, p] of configs) {
  const r = run(p);
  const diff = (r.cagr - r.bCagr);
  console.log(name.padEnd(28), (r.cagr.toFixed(1) + '%').padStart(7), (r.ret.toFixed(0) + '%').padStart(8),
    (r.dd.toFixed(0) + '%').padStart(7), (r.cashPct.toFixed(0) + '%').padStart(6),
    (r.beat.toFixed(0) + '%').padStart(8), '   ' + (diff >= 0 ? '+' : '') + diff.toFixed(1) + '% ' + (diff >= 0 ? 'BEATS' : 'lags'));
}
