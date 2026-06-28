"""
patch-divergence.py  —  upgrade the board's divergence detector to the accurate
TradingView "RSI Divergence Indicator" method (pivots on the RSI line, candle
high/low checked at those pivots). Run once:  python patch-divergence.py
Safe: it verifies the file first and refuses to write if anything looks wrong.
"""
import re, sys, shutil

PATH = "regime-board.html"
raw = open(PATH, "rb").read()
text = raw.decode("utf-8")
crlf = "\r\n" in text
nl = "\r\n" if crlf else "\n"

# Safety checks: make sure this is the real, intact board file
if "FearGreedCell" not in text:
    sys.exit("ABORT: this file looks corrupted/incomplete (no FearGreedCell). Not patching.")
if text.count("function rsiSeries") < 1:
    sys.exit("ABORT: rsiSeries() missing - wrong file version. Not patching.")
m = re.search(r"function\s+detectDivergence\s*\(", text)
if not m:
    sys.exit("ABORT: detectDivergence() not found. Not patching.")

i = m.start()
j = text.index("function computeAllDivergences", i)

NEW = '''function pivotsLR(arr, lbL, lbR) {
  const highs = [], lows = [];
  for (let i = lbL; i < arr.length - lbR; i++) {
    let isH = true, isL = true;
    for (let j = i - lbL; j <= i + lbR; j++) { if (j === i) continue; if (arr[j] >= arr[i]) isH = false; if (arr[j] <= arr[i]) isL = false; }
    if (isH) highs.push(i); if (isL) lows.push(i);
  }
  return { highs, lows };
}
// TradingView "RSI Divergence Indicator" method: pivots on the RSI line; price checked at those bars.
function detectDivergence(closes, highs, lows) {
  const lbL = 5, lbR = 5, gapLo = 5, gapHi = 60;
  if (!closes || closes.length < lbL + lbR + 12) return null;
  const hi = (highs && highs.length === closes.length) ? highs : closes;
  const lo = (lows && lows.length === closes.length) ? lows : closes;
  const osc = rsiSeries(closes, 14);
  const piv = pivotsLR(osc, lbL, lbR);
  const last = closes.length - 1;
  const freshOK = (i) => (last - i) <= lbR + 5;
  let best = null;
  const oL = piv.lows.filter(i => osc[i] != null);
  if (oL.length >= 2) { const b = oL[oL.length-1], a = oL[oL.length-2], gap = b - a;
    if (freshOK(b) && gap >= gapLo && gap <= gapHi && osc[b] > osc[a] && lo[b] < lo[a]) best = { dir:'bull', strength: Math.round(osc[b]-osc[a]), idx: b }; }
  const oH = piv.highs.filter(i => osc[i] != null);
  if (oH.length >= 2) { const b = oH[oH.length-1], a = oH[oH.length-2], gap = b - a;
    if (freshOK(b) && gap >= gapLo && gap <= gapHi && osc[b] < osc[a] && hi[b] > hi[a] && (!best || b > best.idx)) best = { dir:'bear', strength: Math.round(osc[a]-osc[b]), idx: b }; }
  return best;
}
'''
block = NEW.replace("\n", nl) + nl
out = text[:i] + block + text[j:]

# Final safety: don't shrink the file dramatically (corruption guard)
if len(out) < len(text) - 2000:
    sys.exit("ABORT: result is unexpectedly smaller - not writing.")

open(PATH, "wb").write(out.encode("utf-8"))
shutil.copy2(PATH, "index.html")

chk = open(PATH, encoding="utf-8").read()
print("Done. pivotsLR added:", "function pivotsLR" in chk, "| FearGreedCell intact:", chk.count("FearGreedCell"), "| size:", len(chk))
print("Next: git add -A then git commit then git push")
