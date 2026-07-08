"""
update-prices.py  ─  Bake all watchlist prices into data/prices.json
════════════════════════════════════════════════════════════════════════

AUTO MODE (recommended — run this once a day):
    python update-prices.py

    Fetches the last 420 calendar days of daily closes from Yahoo Finance
    for every ticker on the board (US, ASX, HK, crypto, commodities) and
    writes them into data/prices.json, which regime-board.html fetches at
    boot. The HTML itself is no longer touched by price updates.
    NOTE: fetch('data/prices.json') is blocked when opening the HTML via
    file:// — use serve.bat (local mini-server) or the live site.

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
    # Watchlist
    "AAPL":       "AAPL",
    "MSFT":       "MSFT",
    "TSLA":       "TSLA",
    "NVDA":       "NVDA",
    "ASML":       "ASML",
    "IVV":        "IVV",
    "PCT":        "PCT",
    "SOUN":       "SOUN",
    "SPCX":       "SPCX",
    # Top 100 US-listed (2026-07-08)
    "NVDA":       "NVDA",
    "AAPL":       "AAPL",
    "GOOGL":      "GOOGL",
    "MSFT":       "MSFT",
    "AMZN":       "AMZN",
    "AVGO":       "AVGO",
    "TSM":        "TSM",
    "TSLA":       "TSLA",
    "META":       "META",
    "MU":         "MU",
    "BRK.B":      "BRK-B",
    "LLY":        "LLY",
    "WMT":        "WMT",
    "AMD":        "AMD",
    "JPM":        "JPM",
    "ASML":       "ASML",
    "ORCL":       "ORCL",
    "XOM":        "XOM",
    "V":          "V",
    "INTC":       "INTC",
    "JNJ":        "JNJ",
    "CSCO":       "CSCO",
    "ARM":        "ARM",
    "LRCX":       "LRCX",
    "CAT":        "CAT",
    "COST":       "COST",
    "MA":         "MA",
    "AMAT":       "AMAT",
    "ABBV":       "ABBV",
    "CVX":        "CVX",
    "BAC":        "BAC",
    "NFLX":       "NFLX",
    "UNH":        "UNH",
    "PLTR":       "PLTR",
    "KO":         "KO",
    "MS":         "MS",
    "GE":         "GE",
    "PG":         "PG",
    "HSBC":       "HSBC",
    "GS":         "GS",
    "HD":         "HD",
    "BABA":       "BABA",
    "IBM":        "IBM",
    "MRK":        "MRK",
    "TXN":        "TXN",
    "KLAC":       "KLAC",
    "AZN":        "AZN",
    "PM":         "PM",
    "DELL":       "DELL",
    "SNDK":       "SNDK",
    "RY":         "RY",
    "MRVL":       "MRVL",
    "QCOM":       "QCOM",
    "NVS":        "NVS",
    "GEV":        "GEV",
    "SHEL":       "SHEL",
    "WFC":        "WFC",
    "TM":         "TM",
    "LIN":        "LIN",
    "RTX":        "RTX",
    "PANW":       "PANW",
    "C":          "C",
    "MUFG":       "MUFG",
    "ANET":       "ANET",
    "ADI":        "ADI",
    "STX":        "STX",
    "SAP":        "SAP",
    "AXP":        "AXP",
    "WDC":        "WDC",
    "TTE":        "TTE",
    "TMUS":       "TMUS",
    "PEP":        "PEP",
    "VZ":         "VZ",
    "MCD":        "MCD",
    "APP":        "APP",
    "NVO":        "NVO",
    "CRWD":       "CRWD",
    "TD":         "TD",
    "AMGN":       "AMGN",
    "APH":        "APH",
    "SAN":        "SAN",
    "NEE":        "NEE",
    "TMO":        "TMO",
    "TJX":        "TJX",
    "GLW":        "GLW",
    "DIS":        "DIS",
    "BA":         "BA",
    "SCCO":       "SCCO",
    "T":          "T",
    "ETN":        "ETN",
    "BLK":        "BLK",
    "GILD":       "GILD",
    "DE":         "DE",
    "CRM":        "CRM",
    "UNP":        "UNP",
    "BUD":        "BUD",
    "ABT":        "ABT",
    "SCHW":       "SCHW",
    "SHOP":       "SHOP",
    "UBER":       "UBER",
    # Commodities (ETFs)
    "GLD":        "GLD",
    "SLV":        "SLV",
    "PPLT":       "PPLT",
    "PALL":       "PALL",
    "CPER":       "CPER",
    "USO":        "USO",
    "BNO":        "BNO",
    "UNG":        "UNG",
    "UGA":        "UGA",
    "DBA":        "DBA",
    "CORN":       "CORN",
    "WEAT":       "WEAT",
    "SOYB":       "SOYB",
    "CANE":       "CANE",
    "DBC":        "DBC",
    "PDBC":       "PDBC",
    "GSG":        "GSG",
    "KRBN":       "KRBN",
    "URA":        "URA",
    "GDX":        "GDX",
    # ASX top 50
    "BHP":        "BHP.AX",
    "CBA":        "CBA.AX",
    "RIO":        "RIO.AX",
    "NEM":        "NEM.AX",
    "WBC":        "WBC.AX",
    "NAB":        "NAB.AX",
    "ANZ":        "ANZ.AX",
    "WES":        "WES.AX",
    "MQG":        "MQG.AX",
    "GMG":        "GMG.AX",
    "FMG":        "FMG.AX",
    "WDS":        "WDS.AX",
    "XYZ":        "XYZ.AX",
    "TLS":        "TLS.AX",
    "CSL":        "CSL.AX",
    "TCL":        "TCL.AX",
    "WOW":        "WOW.AX",
    "RMD":        "RMD.AX",
    "QBE":        "QBE.AX",
    "ALL":        "ALL.AX",
    "COL":        "COL.AX",
    "SIG":        "SIG.AX",
    "NST":        "NST.AX",
    "AMC":        "AMC.AX",
    "STO":        "STO.AX",
    "AAI":        "AAI.AX",
    "BXB":        "BXB.AX",
    "EVN":        "EVN.AX",
    "CPU":        "CPU.AX",
    "PLS":        "PLS.AX",
    "NWS":        "NWS.AX",
    "S32":        "S32.AX",
    "SCG":        "SCG.AX",
    "SUN":        "SUN.AX",
    "JHX":        "JHX.AX",
    "FPH":        "FPH.AX",
    "ORG":        "ORG.AX",
    "REA":        "REA.AX",
    "IAG":        "IAG.AX",
    "LYC":        "LYC.AX",
    "PME":        "PME.AX",
    "SGH":        "SGH.AX",
    "SOL.AX":     "SOL.AX",
    "BSL":        "BSL.AX",
    "APA":        "APA.AX",
    "QAN":        "QAN.AX",
    "MPL":        "MPL.AX",
    "MIN":        "MIN.AX",
    "MEZ":        "MEZ.AX",
    "TLC":        "TLC.AX",
    # Hong Kong top 30
    "0700.HK":    "0700.HK",
    "1398.HK":    "1398.HK",
    "1288.HK":    "1288.HK",
    "0939.HK":    "0939.HK",
    "0005.HK":    "0005.HK",
    "3988.HK":    "3988.HK",
    "0857.HK":    "0857.HK",
    "3750.HK":    "3750.HK",
    "9988.HK":    "9988.HK",
    "0941.HK":    "0941.HK",
    "0883.HK":    "0883.HK",
    "1088.HK":    "1088.HK",
    "3968.HK":    "3968.HK",
    "2318.HK":    "2318.HK",
    "2628.HK":    "2628.HK",
    "1211.HK":    "1211.HK",
    "2899.HK":    "2899.HK",
    "0300.HK":    "0300.HK",
    "1299.HK":    "1299.HK",
    "0981.HK":    "0981.HK",
    "3328.HK":    "3328.HK",
    "1658.HK":    "1658.HK",
    "1810.HK":    "1810.HK",
    "0386.HK":    "0386.HK",
    "0728.HK":    "0728.HK",
    "9999.HK":    "9999.HK",
    "2388.HK":    "2388.HK",
    "3690.HK":    "3690.HK",
    "0388.HK":    "0388.HK",
    "9633.HK":    "9633.HK",
    # Global Indices (ETFs)
    "SPY":        "SPY",
    "QQQ":        "QQQ",
    "DIA":        "DIA",
    "EWJ":        "EWJ",
    "EWG":        "EWG",
    "EWU":        "EWU",
    "FXI":        "FXI",
    "INDA":       "INDA",
    "EEM":        "EEM",
    # Forex
    "EURUSD":     "EURUSD=X",
    "GBPUSD":     "GBPUSD=X",
    "USDJPY":     "USDJPY=X",
    "AUDUSD":     "AUDUSD=X",
    "USDCAD":     "USDCAD=X",
    "DXY":        "DX-Y.NYB",
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
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "SOL": "solana",
    "TRX": "tron",
    "HYPE": "hyperliquid",
    "DOGE": "dogecoin",
    "LEO": "leo-token",
    "ZEC": "zcash",
    "XLM": "stellar",
    "ADA": "cardano",
    "XMR": "monero",
    "LINK": "chainlink",
    "BCH": "bitcoin-cash",
    "TON": "the-open-network",
    "LTC": "litecoin",
    "HBAR": "hedera-hashgraph",
    "SUI": "sui",
    "AVAX": "avalanche-2",
    "CRO": "crypto-com-chain",
    "NEAR": "near",
    "SHIB": "shiba-inu",
    "TAO": "bittensor",
    "UNI": "uniswap",
    "OKB": "okb",
    "ONDO": "ondo-finance",
    "DOT": "polkadot",
    "AAVE": "aave",
    "MNT": "mantle",
    "WLD": "worldcoin-wld",
    "SKY": "sky",
    "ICP": "internet-computer",
    "PI": "pi-network",
    "PEPE": "pepe",
    "ETC": "ethereum-classic",
    "MORPHO": "morpho",
    "ATOM": "cosmos",
    "RENDER": "render-token",
    "POL": "polygon-ecosystem-token",
    "KAS": "kaspa",
    "QNT": "quant-network",
    "JUP": "jupiter-exchange-solana",
    "FIL": "filecoin",
    "INJ": "injective-protocol",
    "ARB": "arbitrum",
    "ALGO": "algorand",
    "VET": "vechain",
    "APT": "aptos",
    "SEI": "sei-network",
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
PE_STOCKS = ["NVDA", "AAPL", "GOOGL", "MSFT", "AMZN", "AVGO", "TSM", "TSLA", "META", "MU", "BRK.B", "LLY", "WMT", "AMD", "JPM", "ASML", "ORCL", "XOM", "V", "INTC", "JNJ", "CSCO", "ARM", "LRCX", "CAT", "COST", "MA", "AMAT", "ABBV", "CVX", "BAC", "NFLX", "UNH", "PLTR", "KO", "MS", "GE", "PG", "HSBC", "GS", "HD", "BABA", "IBM", "MRK", "TXN", "KLAC", "AZN", "PM", "DELL", "SNDK", "RY", "MRVL", "QCOM", "NVS", "GEV", "SHEL", "WFC", "TM", "LIN", "RTX", "PANW", "C", "MUFG", "ANET", "ADI", "STX", "SAP", "AXP", "WDC", "TTE", "TMUS", "PEP", "VZ", "MCD", "APP", "NVO", "CRWD", "TD", "AMGN", "APH", "SAN", "NEE", "TMO", "TJX", "GLW", "DIS", "BA", "SCCO", "T", "ETN", "BLK", "GILD", "DE", "CRM", "UNP", "BUD", "ABT", "SCHW", "SHOP", "UBER"]

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

def data_json_path(script_dir: str) -> str:
    return os.path.join(script_dir, "data", "prices.json")


def load_data(path: str) -> dict:
    """Read data/prices.json ({updated, prices, pe, ohlc, weekly}) or an empty skeleton."""
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return {
            "updated": d.get("updated"),
            "prices":  d.get("prices") or {},
            "pe":      d.get("pe")     or {},
            "ohlc":    d.get("ohlc")   or {},
            "weekly":  d.get("weekly") or {},
        }
    except Exception:
        return {"updated": None, "prices": {}, "pe": {}, "ohlc": {}, "weekly": {}}


def save_data(path: str, data: dict):
    """Atomically write data/prices.json (write tmp file, then replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(tmp, path)
    print(f"  ✓  data/prices.json written ({os.path.getsize(path):,} bytes)")


def sync_index(html_path: str):
    """Copy regime-board.html to index.html so GitHub Pages serves the latest version."""
    import shutil
    index_path = os.path.join(os.path.dirname(html_path), "index.html")
    shutil.copy2(html_path, index_path)
    print(f"  ✓  index.html synced")


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

        dp = data_json_path(script_dir)
        d = load_data(dp)
        d["prices"][board_name] = closes
        save_data(dp, d)
        print(f"\n✓  {board_name} written to data/prices.json")
        return

    # ── Auto mode: Yahoo Finance for ALL tickers ──────────────────────────────
    print("=" * 60)
    print("  Trend Momo — Price Update")
    print(f"  Fetching {len(ALL_TICKERS)} tickers from Yahoo Finance")
    print("=" * 60)
    print()

    dp = data_json_path(script_dir)
    d = load_data(dp)
    prices = d["prices"]
    ohlc   = d["ohlc"]     # merge: tickers that fail today keep yesterday's bars
    weekly = d["weekly"]

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

    d["pe"].update(pe_out)   # merge: failed P/E fetches keep the previous value
    save_data(dp, d)
    sync_index(html_path)

    print()
    print("=" * 60)
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  ✓  Done at {ts}  ({ok_count} ok, {err_count} failed)")
    print(f"  data/prices.json updated (regime-board.html untouched).")
    print("=" * 60)
    print()

    all_keys = list(ALL_TICKERS) + list(CRYPTO_CG)
    missing = [t for t in all_keys if not prices.get(t)]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        print("  Run again or use --csv to import missing tickers manually.\n")


if __name__ == "__main__":
    main()
