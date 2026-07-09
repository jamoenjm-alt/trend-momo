#!/usr/bin/env python3
"""
WATER strategy - 10-year backtest runner.

What it does (run from your machine, where Yahoo works):
  1. Extracts the site's EXACT signal math (buyScore/computeSignals/...) out of
     regime-board.html into water-signals.js  -> backtest can't drift from the page.
  2. Pulls ~10 years of daily closes for the equity/ETF universe from Yahoo
     (reusing update-prices.py's fetch_yahoo + symbol map).
  3. Runs water-backtest.js and prints the 10-year result + writes water-equity.json.

Usage:   python water.py
"""
import os, re, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "regime-board.html")
YEARS = 10
MINBARS = 2400          # ~9.5y; a name needs this much history to enter the backtest universe

# ---- 1. extract the signal bundle (proven brace-matcher) --------------------
def _extract_fn(name, js):
    mt = re.search(r'function\s+' + re.escape(name) + r'\s*\(', js)
    i = js.index('{', mt.end() - 1); depth = 0
    for k in range(i, len(js)):
        if js[k] == '{': depth += 1
        elif js[k] == '}':
            depth -= 1
            if depth == 0: return js[mt.start():k + 1]
    raise RuntimeError("unbalanced fn " + name)

def _extract_const(name, js):
    mt = re.search(r'const\s+' + re.escape(name) + r'\s*=\s*', js)
    j = mt.end(); op = js[j]; cl = ']' if op == '[' else '}'; depth = 0
    for k in range(j, len(js)):
        if js[k] == op: depth += 1
        elif js[k] == cl:
            depth -= 1
            if depth == 0: return js[mt.start():k + 1] + ';'
    raise RuntimeError("unbalanced const " + name)

def build_signals():
    src = open(HTML, encoding='utf-8').read()
    js = re.search(r'<script type="module">(.*?)</script>', src, re.DOTALL).group(1)
    parts = [_extract_const('MA_PAIRS', js), _extract_const('WATCHLIST', js)]
    for fn in ['sma', 'scoreToRegime', 'computeSignals', 'buyScore']:
        parts.append(_extract_fn(fn, js))
    parts.append("module.exports={MA_PAIRS,WATCHLIST,computeSignals,buyScore,scoreToRegime,sma};")
    out = os.path.join(HERE, 'water-signals.js')
    open(out, 'w', encoding='utf-8').write("\n\n".join(parts))
    print("  extracted signal math -> water-signals.js")

# ---- 2. fetch ~10y daily closes for the equity universe ---------------------
def fetch_history():
    import importlib.util
    spec = importlib.util.spec_from_file_location("update_prices", os.path.join(HERE, "update-prices.py"))
    up = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(up)
    hist = {}
    for board, ysym in up.ALL_TICKERS.items():
        if ysym.endswith('-USD') or ysym.endswith('=X'):   # skip crypto / forex
            continue
        print(f"  {board:10s} ({ysym}) ...", end=" ", flush=True)
        try:
            closes, highs, lows = up.fetch_yahoo(ysym, days=YEARS * 365 + 30)
            if closes and len(closes) > 200:
                hist[board] = closes
                print(f"{len(closes)} bars")
            else:
                print("skip (no data)")
        except Exception as e:
            print("skip", e)
    json.dump(hist, open(os.path.join(HERE, 'water-history.json'), 'w'))
    print(f"  wrote water-history.json ({len(hist)} tickers)")
    return hist

# ---- 3. run the engine ------------------------------------------------------
def run_engine():
    env = dict(os.environ); env['MINBARS'] = str(MINBARS)
    node = 'node'
    r = subprocess.run([node, 'water-backtest.js'], cwd=HERE, env=env)
    if r.returncode != 0:
        print("engine failed - is Node.js installed and on PATH?")

if __name__ == '__main__':
    print("WATER 10-year backtest")
    print("1) extracting signal math from regime-board.html ...")
    build_signals()
    print(f"2) fetching ~{YEARS}y of daily prices from Yahoo (this takes a couple of minutes) ...")
    fetch_history()
    print("3) running the backtest ...")
    run_engine()
