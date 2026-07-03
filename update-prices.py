"""
update-prices.py  ─  Bake all watchlist prices into regime-board.html
════════════════════════════════════════════════════════════════════════

AUTO MODE (recommended — run this once a day):
    python update-prices.py

    Fetches the last 420 calendar days of daily closes from Yahoo Finance
    for every ticker on the board (US, ASX, HK, crypto, commodities) and
    writes them into the STATIC_PRICES block inside regime-board.html.
    After running, just open the HTML — no API calls on page load.

CSV MODE (manual override for any ticker):
    python update-prices.py --csv ASML-history.csv ASML
    python update-prices.py --csv MQG-history.csv  MQG

    Imports a stockanalysis.com "History" CSV (Date, Open, High, Low,
    Close, Adj. Close, Change, Volume). Merges with existing prices.

SCHEDULE (optional):
    Set up a Windows Scheduled Task to run this each morning so the
    board always has fresh data when you open it.
"""

import json
import re
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

# ── All watchlist tickers → Yahoo Finance symbols ─────────────────────────────
# Keeping the board ticker as key (what the HTML uses) and Yahoo symbol as value.
ALL_TICKERS = {
    # ── Watchlist ─────────────────────────────────────────────────────────────
    "AAPL":    "AAPL",
    "MSFT":    "MSFT",
    "TSLA":    "TSLA",
    "NVDA":    "NVDA",
    "ASML":    "ASML",
    "IVV":     "IVV",
    "PCT":     "PCT",
    "SOUN":    "SOUN",
    "SPCX":    "SPCX",

    # ── Top 20 US ─────────────────────────────────────────────────────────────
    "AMZN":    "AMZN",
    "GOOGL":   "GOOGL",
    "META":    "META",
    "BRK.B":   "BRK-B",
    "AVGO":    "AVGO",
    "JPM":     "JPM",
    "LLY":     "LLY",
    "V":       "V",
    "UNH":     "UNH",
    "ORCL":    "ORCL",
    "MA":      "MA",
    "XOM":     "XOM",
    "NFLX":    "NFLX",
    "COST":    "COST",
    "WMT":     "WMT",
    "HD":      "HD",

    # ── Crypto is fetched from CoinGecko (see CRYPTO_CG below), NOT Yahoo ───────
    #    CoinGecko ids are canonical, so a bad id yields no data (honest N/A) rather
    #    than Yahoo's silent wrong-token problem (e.g. plain TON-USD = wrong coin).

    # ── Commodities (ETFs) ────────────────────────────────────────────────────
    "GLD":     "GLD",
    "SLV":     "SLV",
    "PALL":    "PALL",
    "PPLT":    "PPLT",

    # ── ASX ───────────────────────────────────────────────────────────────────
    "MQG":     "MQG.AX",
    "A2M":     "A2M.AX",
    "CBA":     "CBA.AX",
    "BHP":     "BHP.AX",
    "WBC":     "WBC.AX",
    "NAB":     "NAB.AX",
    "WES":     "WES.AX",
    "CSL":     "CSL.AX",
    "WDS":     "WDS.AX",
    "FMG":     "FMG.AX",
    "ANZ":     "ANZ.AX",

    # ── Hong Kong ─────────────────────────────────────────────────────────────
    "1211.HK": "1211.HK",

    # ── Global Indices (ETFs) ─────────────────────────────────────────────────
    "SPY":     "SPY",
    "QQQ":     "QQQ",
    "DIA":     "DIA",
    "EWJ":     "EWJ",
    "EWG":     "EWG",
    "EWU":     "EWU",
    "FXI":     "FXI",
    "INDA":    "INDA",
    "EEM":     "EEM",

    # ── Forex ─────────────────────────────────────────────────────────────────
    "EURUSD":  "EURUSD=X",
    "GBPUSD":  "GBPUSD=X",
    "USDJPY":  "USDJPY=X",
    "AUDUSD":  "AUDUSD=X",
    "USDCAD":  "USDCAD=X",
    "DXY":     "DX-Y.NYB",
}

# Days of history to fetch (need 252 trading days ≈ 365 calendar + buffer)
HISTORY_DAYS = 420

# Pause between Yahoo Finance requests to be polite (seconds)
REQUEST_PAUSE = 0.4


# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_yahoo(yahoo_symbol: str, days: int = HISTORY_DAYS, retries: int = 3, interval: str = "1d") -> tuple:
    """
    Fetch daily (or weekly, interval="1wk") closes/highs/lows/volumes from Yahoo Finance v8 API.
    Returns (closes, highs, lows, volumes) — lists of floats oldest first, or ([], [], [], []) on error.
    Retries up to `retries` times with exponential backoff on connection errors.
    """
    end   = int(datetime.now(timezone.utc).timestamp())
    start = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    encoded = urllib.parse.quote(yahoo_symbol)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        f"?interval={interval}&period1={start}&period2={end}&events=history"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept":          "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for attempt in range(retries):
        if attempt > 0:
            wait = 2 ** attempt  # 2s, 4s
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode("utf-8"))

            result = raw.get("chart", {}).get("result", [None])[0]
            if not result:
                err = raw.get("chart", {}).get("error", {})
                print(f"no data ({err.get('description', 'empty response')})")
                return [], [], [], []

            q = result["indicators"]["quote"][0]
            closes_raw = q.get("close", [])
            highs_raw  = q.get("high", []);   highs_raw += [None] * (len(closes_raw) - len(highs_raw))
            lows_raw   = q.get("low", []);    lows_raw  += [None] * (len(closes_raw) - len(lows_raw))
            vols_raw   = q.get("volume", []); vols_raw  += [None] * (len(closes_raw) - len(vols_raw))
            timestamps = result.get("timestamp", [])
            rows = sorted(
                ((ts, c, h, l, v) for ts, c, h, l, v in zip(timestamps, closes_raw, highs_raw, lows_raw, vols_raw) if c is not None),
                key=lambda x: x[0],
            )
            closes = [round(c, 4) for _, c, _, _, _ in rows]
            highs  = [round(h if h is not None else c, 4) for _, c, h, _, _ in rows]
            lows   = [round(l if l is not None else c, 4) for _, c, _, l, _ in rows]
            vols   = [int(v) if v is not None else 0 for _, _, _, _, v in rows]
            return closes, highs, lows, vols

        except Exception as e:
            if attempt < retries - 1:
                print(f"retry {attempt+1}...", end=" ", flush=True)
            else:
                print(f"ERROR: {e}")
    return [], [], [], []


# ── All watchlist crypto → CoinGecko coin ids ────────────────────────────────
# CoinGecko ids are unambiguous; this is the same source the board's live path uses.
CRYPTO_CG = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple",
    "BNB": "binancecoin", "ADA": "cardano", "LINK": "chainlink",
    "TON": "the-open-network", "AVAX": "avalanche-2", "SUI": "sui",
    "DOGE": "dogecoin", "DOT": "polkadot", "TRX": "tron", "MATIC": "matic-network",
    "LTC": "litecoin", "BCH": "bitcoin-cash", "APT": "aptos", "NEAR": "near",
    "ARB": "arbitrum", "ATOM": "cosmos", "OP": "optimism",
    "INJ": "injective-protocol", "HBAR": "hedera-hashgraph", "FIL": "filecoin",
    "AAVE": "aave", "VET": "vechain", "XLM": "stellar", "ETC": "ethereum-classic",
    "ALGO": "algorand", "UNI": "uniswap", "ICP": "internet-computer",
    "GRT": "the-graph", "SAND": "the-sandbox", "MANA": "decentraland",
    "MKR": "maker", "RUNE": "thorchain", "LDO": "lido-dao", "STX": "blockstack",
    "FTM": "fantom", "SEI": "sei-network", "EGLD": "elrond-erd-2",
    "DYDX": "dydx-chain", "PEPE": "pepe", "FLOKI": "floki", "WIF": "dogwifcoin",
}

# CoinGecko free tier is rate-limited — pause longer between calls than Yahoo.
CG_KEY = ""   # <-- paste a FREE CoinGecko Demo API key here (coingecko.com/en/api/pricing -> Demo)
              #     to stop the 429 rate-limit errors. Leave "" to use the throttled public tier.
CG_PAUSE = 4.0

def fetch_coingecko(cg_id, days=365, retries=3):
    """Daily close prices (oldest first) from CoinGecko, or [] on error."""
    url = (f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
           f"?vs_currency=usd&days={days}")   # days>=90 returns daily granularity
    if CG_KEY:
        url += f"&x_cg_demo_api_key={CG_KEY}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    for attempt in range(retries):
        if attempt > 0:
            time.sleep(5 * attempt)   # back off (CoinGecko 429s under load)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            prices = raw.get("prices", [])
            return [round(float(p[1]), 6) for p in prices if p and p[1] is not None]
        except Exception as e:
            if attempt < retries - 1:
                print(f"retry {attempt+1}...", end=" ", flush=True)
            else:
                print(f"ERROR: {e}")
    return []

# US stocks whose trailing P/E we auto-refresh from stockanalysis (overrides the
# curated PE_RATIOS in the HTML; falls back to the curated value if a fetch fails).
PE_STOCKS = ["PLTR","AAPL","MSFT","TSLA","NVDA","ASML","AMZN","GOOGL","META","BRK.B",
             "AVGO","JPM","LLY","V","UNH","ORCL","MA","XOM","NFLX","COST","WMT","HD"]

def fetch_pe(ticker):
    """Current trailing P/E from stockanalysis, or None on error / not meaningful."""
    url = f"https://stockanalysis.com/api/symbol/s/{ticker.lower()}/overview"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            j = json.loads(resp.read().decode("utf-8"))
        pe = (j.get("data") or {}).get("peRatio")
        if pe in (None, "", "-", "n/a", "N/A"):
            return None
        v = float(str(pe).replace(",", ""))
        return round(v, 1) if 0 < v < 100000 else None
    except Exception:
        return None

def inject_live_pe(pe_dict, html_path):
    """Replace the @@LIVE_PE@@ block with freshly fetched trailing P/E values."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    ms, me = "// @@LIVE_PE_START@@", "// @@LIVE_PE_END@@"
    i, j = content.find(ms), content.find(me)
    if i == -1 or j == -1:
        print("  (LIVE_PE markers not found - skipping P/E inject)")
        return False
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = (ms + "\n" +
            f"// trailing P/E auto-refreshed {ts} from stockanalysis\n" +
            f"window.LIVE_PE = {json.dumps(pe_dict, separators=(',', ':'))};\n" + me)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content[:i] + body + content[j + len(me):])
    return True


def inject_ohlc(ohlc_dict, html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    ms, me = "// @@STATIC_OHLC_START@@", "// @@STATIC_OHLC_END@@"
    i, j = content.find(ms), content.find(me)
    if i == -1 or j == -1:
        print("  (STATIC_OHLC markers not found - skipping)")
        return False
    body = ms + "\n" + f"window.STATIC_OHLC = {json.dumps(ohlc_dict, separators=(',', ':'))};\n" + me
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content[:i] + body + content[j + len(me):])
    return True


def inject_weekly(weekly_dict, html_path):
    """Replace the @@STATIC_WEEKLY@@ block with true weekly OHLC (interval=1wk from Yahoo)."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    ms, me = "// @@STATIC_WEEKLY_START@@", "// @@STATIC_WEEKLY_END@@"
    i, j = content.find(ms), content.find(me)
    if i == -1 or j == -1:
        print("  (STATIC_WEEKLY markers not found - skipping)")
        return False
    body = ms + "\n" + f"window.STATIC_WEEKLY = {json.dumps(weekly_dict, separators=(',', ':'))};\n" + me
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content[:i] + body + content[j + len(me):])
    return True


def inject_into_html(prices: dict, html_path: str):
    """
    Replace the @@STATIC_PRICES_START@@ … @@STATIC_PRICES_END@@ block
    in regime-board.html with the latest prices dict.
    Uses plain string splitting (not regex) to avoid corruption of the React tail.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    marker_start = "// @@STATIC_PRICES_START@@"
    marker_end   = "// @@STATIC_PRICES_END@@"

    start_idx = content.find(marker_start)
    end_idx   = content.find(marker_end)

    if start_idx == -1:
        print("\n✗  START marker not found in regime-board.html.")
        sys.exit(1)
    if end_idx == -1:
        print("\n✗  END marker not found in regime-board.html.")
        print("   Run the rebuild script or contact support.")
        sys.exit(1)

    before = content[:start_idx]
    after  = content[end_idx + len(marker_end):]

    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_str = json.dumps(prices, separators=(",", ":"))

    updated = (
        before +
        marker_start + "\n" +
        f"// All prices last updated {ts} by update-prices.py\n" +
        f"window.STATIC_PRICES = {json_str};\n" +
        marker_end +
        after
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated)


def sync_index(html_path: str):
    """Copy regime-board.html to index.html so GitHub Pages serves the latest version."""
    import shutil
    index_path = os.path.join(os.path.dirname(html_path), "index.html")
    shutil.copy2(html_path, index_path)
    print(f"  ✓  index.html synced")


def load_existing_static_prices(html_path: str) -> dict:
    """Read the current STATIC_PRICES dict out of the HTML (to merge/preserve)."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"window\.STATIC_PRICES\s*=\s*(\{.*?\});", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def parse_stockanalysis_csv(csv_path: str) -> list:
    """
    Parse a stockanalysis.com history CSV.
    Columns: Date, Open, High, Low, Close, Adj. Close, Change, Volume
    Returns list of floats (oldest first).
    """
    import csv as csv_mod
    closes = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        rows = sorted(reader, key=lambda r: r["Date"])
        for row in rows:
            try:
                val = row.get("Adj. Close") or row.get("Close") or ""
                closes.append(float(val.replace(",", "")))
            except (ValueError, KeyError):
                pass
    return closes


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path  = os.path.join(script_dir, "regime-board.html")

    if not os.path.exists(html_path):
        print(f"✗  regime-board.html not found at: {html_path}")
        sys.exit(1)

    # ── CSV mode: python update-prices.py --csv FILE.csv TICKER ──────────────
    if len(sys.argv) >= 4 and sys.argv[1] == "--csv":
        csv_file   = sys.argv[2]
        board_name = sys.argv[3].upper()
        csv_path   = csv_file if os.path.isabs(csv_file) else os.path.join(script_dir, csv_file)

        if not os.path.exists(csv_path):
            print(f"✗  CSV not found: {csv_path}")
            sys.exit(1)

        print(f"Importing {board_name} from {os.path.basename(csv_path)} …")
        closes = parse_stockanalysis_csv(csv_path)
        if not closes:
            print("✗  No data parsed. Check CSV format.")
            sys.exit(1)
        print(f"  ✓  {len(closes)} closes  (first={closes[0]:.2f}, last={closes[-1]:.2f})")

        prices = load_existing_static_prices(html_path)
        prices[board_name] = closes
        inject_into_html(prices, html_path)
        sync_index(html_path)
        print(f"\n✓  {board_name} injected into regime-board.html")
        return

    # ── Auto mode: Yahoo Finance for ALL tickers ──────────────────────────────
    print("=" * 60)
    print("  Trend Momo — Price Update")
    print(f"  Fetching {len(ALL_TICKERS)} tickers from Yahoo Finance")
    print("=" * 60)
    print()

    prices = load_existing_static_prices(html_path)
    ohlc = {}
    weekly = {}

    ok_count  = 0
    err_count = 0

    for board_ticker, yahoo_symbol in ALL_TICKERS.items():
        label = f"{board_ticker:10s} ({yahoo_symbol})"
        print(f"  → {label:28s}", end="  ", flush=True)

        closes, highs, lows, vols = fetch_yahoo(yahoo_symbol)
        if closes:
            prices[board_ticker] = closes
            ohlc[board_ticker] = {"h": highs[-200:], "l": lows[-200:], "v": vols[-200:]}
            ok_count += 1
            print(f"✓  {len(closes)} closes   last={closes[-1]:,.3f}")
        else:
            err_count += 1
            if board_ticker in prices:
                print("⚠  fetch failed — keeping previous data")
            else:
                print("✗  no data")

        time.sleep(REQUEST_PAUSE)

        # True weekly bars (interval=1wk) for honest weekly RSI divergences.
        wc, wh, wl, _wv = fetch_yahoo(yahoo_symbol, days=1500, interval="1wk")
        if wc and len(wc) >= 30:
            weekly[board_ticker] = {"c": wc[-200:], "h": wh[-200:], "l": wl[-200:]}
        time.sleep(REQUEST_PAUSE)

    # ── Crypto via CoinGecko (staggered to respect free-tier rate limits) ──────
    # Major coins refresh EVERY run; the long-tail alts are split across two days
    # (each alt ~every 2nd day). Coins skipped today keep their previous data, so
    # nothing goes blank — we just maximise how much stays freshly updated.
    cg_items = list(CRYPTO_CG.items())
    CRYPTO_DAILY = 12                                   # first N (majors) every day
    core = cg_items[:CRYPTO_DAILY]
    alts = cg_items[CRYPTO_DAILY:]
    todays_alts = alts[datetime.now().toordinal() % 2 :: 2]   # alternating half
    todays_crypto = core + todays_alts
    print()
    print(f"  Fetching {len(todays_crypto)} of {len(CRYPTO_CG)} cryptos from CoinGecko")
    print(f"  (majors daily + half the alts; the other half refreshes next run)")
    for board_ticker, cg_id in todays_crypto:
        print(f"  → {board_ticker:8s} ({cg_id:22s})", end="  ", flush=True)
        closes = fetch_coingecko(cg_id)
        if closes and len(closes) >= 21:
            prices[board_ticker] = closes
            ok_count += 1
            print(f"✓  {len(closes)} closes   last={closes[-1]:,.4f}")
        else:
            err_count += 1
            print("⚠  kept previous" if board_ticker in prices else "✗  no data")
        time.sleep(CG_PAUSE)

    # -- Trailing P/E from stockanalysis (auto-refresh; curated PE_RATIOS is fallback) --
    print()
    print(f"  Fetching trailing P/E for {len(PE_STOCKS)} stocks from stockanalysis")
    pe_out = {}
    for t in PE_STOCKS:
        v = fetch_pe(t)
        if v is not None:
            pe_out[t] = v
        print(f"  -> {t:8} P/E {v if v is not None else '- (keeping curated)'}")
        time.sleep(0.3)
    print(f"  P/E refreshed for {len(pe_out)} / {len(PE_STOCKS)} stocks")

    if ok_count == 0:
        print("\n✗  Nothing fetched. Check your internet connection.")
        sys.exit(1)

    inject_into_html(prices, html_path)
    if pe_out:
        inject_live_pe(pe_out, html_path)
    if ohlc:
        inject_ohlc(ohlc, html_path)
    if weekly:
        inject_weekly(weekly, html_path)
    sync_index(html_path)

    print()
    print("=" * 60)
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  ✓  Done at {ts}  ({ok_count} ok, {err_count} failed)")
    print(f"  regime-board.html + index.html updated.")
    print("=" * 60)
    print()

    all_keys = list(ALL_TICKERS) + list(CRYPTO_CG)
    missing = [t for t in all_keys if not prices.get(t)]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        print("  Run again or use --csv to import missing tickers manually.\n")


if __name__ == "__main__":
    main()
