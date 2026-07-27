"""
update-property.py  ─  Bake Australian property data into data/property.json
════════════════════════════════════════════════════════════════════════════

Source: SQM Research free chart pages (sqmresearch.com.au). Each page embeds
its full series as a JS literal:  var data = [{...}, ...]  — parsed here with
a bracket-balance scan + json.loads.

Per region we fetch 5 pages:
  asking-property-prices  weekly  {date, houses_all, houses_3, units_all, units_2, combined}
  weekly-rents            weekly  same keys
  rental-yield            weekly  {date, houses_all, houses_3, units_all, units_2}
  vacancy-rates           monthly {year, month, listings, properties, vr}
  total-property-listings monthly {year, month, r30, r60, r90, r180, r180p}

Capitals use ?region=<slug>&type=c (city-wide index); towns use ?postcode=NNNN
(canonical postcode); National uses ?national=1; Capital Avg uses ?avg=1.

Usage:
    python update-property.py            # bake everything (~5 min, 0.5s/req)
    python update-property.py SYD NEW    # bake only listed region codes

Merge semantics: regions that fail today keep yesterday's data (same policy
as update-prices.py). Output written atomically (tmp + os.replace).

NOTE: SQM data is published for personal reference. Attribute SQM on the
board; do not resell.
"""

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

BASE = "https://sqmresearch.com.au/property/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "property.json")
SLEEP = 0.5
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ── Region list ──────────────────────────────────────────────────────────────
# code: (name, state, kind, param)
#   kind 'city'     → region=<param>&type=c
#   kind 'postcode' → postcode=<param>
#   kind 'national' → national=1     kind 'avg' → avg=1
REGIONS = {
    # National
    "AUS":  ("Australia (National)", "NAT", "national", ""),
    "CAP8": ("Capital City Average", "NAT", "avg", ""),
    # NSW
    "SYD": ("Sydney",         "NSW", "city",     "nsw-Sydney"),
    "NEW": ("Newcastle",      "NSW", "postcode", "2300"),
    "WOL": ("Wollongong",     "NSW", "postcode", "2500"),
    "GOS": ("Central Coast (Gosford)", "NSW", "postcode", "2250"),
    "PMQ": ("Port Macquarie", "NSW", "postcode", "2444"),
    "CFS": ("Coffs Harbour",  "NSW", "postcode", "2450"),
    "TMW": ("Tamworth",       "NSW", "postcode", "2340"),
    "WGA": ("Wagga Wagga",    "NSW", "postcode", "2650"),
    "ALB": ("Albury",         "NSW", "postcode", "2640"),
    "DBO": ("Dubbo",          "NSW", "postcode", "2830"),
    "ORG": ("Orange",         "NSW", "postcode", "2800"),
    "BXT": ("Bathurst",       "NSW", "postcode", "2795"),
    "BYR": ("Byron Bay",      "NSW", "postcode", "2481"),
    # VIC
    "MEL": ("Melbourne",      "VIC", "city",     "vic-Melbourne"),
    "GEE": ("Geelong",        "VIC", "postcode", "3220"),
    "BAL": ("Ballarat",       "VIC", "postcode", "3350"),
    "BEN": ("Bendigo",        "VIC", "postcode", "3550"),
    "SHP": ("Shepparton",     "VIC", "postcode", "3630"),
    "MIL": ("Mildura",        "VIC", "postcode", "3500"),
    "WRN": ("Warrnambool",    "VIC", "postcode", "3280"),
    "TRA": ("Traralgon",      "VIC", "postcode", "3844"),
    "WOD": ("Wodonga",        "VIC", "postcode", "3690"),
    # QLD
    "BNE": ("Brisbane",       "QLD", "city",     "qld-Brisbane"),
    "GC":  ("Gold Coast (Southport)",      "QLD", "postcode", "4215"),
    "SC":  ("Sunshine Coast (Maroochydore)", "QLD", "postcode", "4558"),
    "CNS": ("Cairns",         "QLD", "postcode", "4870"),
    "TSV": ("Townsville",     "QLD", "postcode", "4810"),
    "TWB": ("Toowoomba",      "QLD", "postcode", "4350"),
    "MKY": ("Mackay",         "QLD", "postcode", "4740"),
    "ROK": ("Rockhampton",    "QLD", "postcode", "4700"),
    "BDB": ("Bundaberg",      "QLD", "postcode", "4670"),
    "HVB": ("Hervey Bay",     "QLD", "postcode", "4655"),
    "GLT": ("Gladstone",      "QLD", "postcode", "4680"),
    # WA
    "PER": ("Perth",          "WA", "city",     "wa-Perth"),
    "MDH": ("Mandurah",       "WA", "postcode", "6210"),
    "BUN": ("Bunbury",        "WA", "postcode", "6230"),
    "GER": ("Geraldton",      "WA", "postcode", "6530"),
    "KAL": ("Kalgoorlie",     "WA", "postcode", "6430"),
    "ALY": ("Albany",         "WA", "postcode", "6330"),
    "BSN": ("Busselton",      "WA", "postcode", "6280"),
    "BRM": ("Broome",         "WA", "postcode", "6725"),
    # SA
    "ADL": ("Adelaide",       "SA", "city",     "sa-Adelaide"),
    "MTG": ("Mount Gambier",  "SA", "postcode", "5290"),
    "WHY": ("Whyalla",        "SA", "postcode", "5600"),
    "MBR": ("Murray Bridge",  "SA", "postcode", "5253"),
    "PTL": ("Port Lincoln",   "SA", "postcode", "5606"),
    "VHB": ("Victor Harbor",  "SA", "postcode", "5211"),
    # TAS
    "HBA": ("Hobart",         "TAS", "city",     "tas-Hobart"),
    "LST": ("Launceston",     "TAS", "postcode", "7250"),
    "DPT": ("Devonport",      "TAS", "postcode", "7310"),
    "BUR": ("Burnie",         "TAS", "postcode", "7320"),
    # ACT / NT
    "CBR": ("Canberra",       "ACT", "city",     "act-Canberra"),
    "DRW": ("Darwin",         "NT",  "city",     "nt-Darwin"),
    "ASP": ("Alice Springs",  "NT",  "postcode", "0870"),
}

PAGES = {
    "price": "asking-property-prices",
    "rent":  "weekly-rents",
    "yield": "rental-yield",
    "vac":   "vacancy-rates",
    "stock": "total-property-listings",
}


def build_url(page, kind, param):
    url = BASE + PAGES[page]
    if kind == "national":
        return url + "?national=1"
    if kind == "avg":
        return url + "?avg=1"
    if kind == "city":
        return url + "?region=" + param + "&type=c"
    return url + "?postcode=" + param


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"    FAIL {url}: {e}")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def extract_series(html):
    """Locate `var data = [ ... ]` and json.loads it via bracket-balance scan."""
    if not html:
        return None
    m = re.search(r"var\s+data\s*=\s*\[", html)
    if not m:
        return None
    start = html.index("[", m.start())
    depth = 0
    for i in range(start, len(html)):
        c = html[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start:i + 1])
                except json.JSONDecodeError as e:
                    print(f"    JSON parse error: {e}")
                    return None
    return None


def month_key(row):
    return "%04d-%02d" % (int(row["year"]), int(row["month"]))


def drop_partial_month(rows):
    """SQM monthly series include the in-progress month with near-zero counts;
    the site's charts hide it. Drop any trailing rows >= the current month."""
    cur = datetime.now(timezone.utc).strftime("%Y-%m")
    return [r for r in rows if month_key(r) < cur]


def pct_rank(vals, x):
    """Percentile (0-100) of x within vals."""
    vals = [v for v in vals if v is not None]
    if not vals or x is None:
        return None
    below = sum(1 for v in vals if v <= x)
    return round(100.0 * below / len(vals), 1)


def bake_region(code, name, state, kind, param):
    out = {"name": name, "state": state, "kind": kind, "param": param}
    ok = False

    # ── weekly asking prices (signal series) ─────────────────────────────
    rows = extract_series(fetch_html(build_url("price", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("combined") or r.get("houses_all")]
        rows.sort(key=lambda r: r["date"])
        px = [int(round(r.get("combined") or r.get("houses_all") or 0)) for r in rows]
        if len(px) >= 60:
            out["px"] = px
            out["px_end"] = rows[-1]["date"]
            last, y_ago = rows[-1], rows[max(0, len(rows) - 53)]
            out["snap_px"] = {
                "h":   int(round(last.get("houses_all") or 0)) or None,
                "h52": int(round(y_ago.get("houses_all") or 0)) or None,
                "u":   int(round(last.get("units_all") or 0)) or None,
                "u52": int(round(y_ago.get("units_all") or 0)) or None,
            }
            ok = True

    # ── weekly rents ─────────────────────────────────────────────────────
    rows = extract_series(fetch_html(build_url("rent", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("combined") or r.get("houses_all")]
        rows.sort(key=lambda r: r["date"])
        if rows:
            val = lambda r: r.get("combined") or r.get("houses_all")
            last, y_ago = rows[-1], rows[max(0, len(rows) - 53)]
            out["rent"] = round(val(last), 1)
            out["rent52"] = round(val(y_ago), 1)
            ok = True

    # ── rental yield (weekly; houses_all preferred) ──────────────────────
    rows = extract_series(fetch_html(build_url("yield", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("houses_all") or r.get("units_all")]
        rows.sort(key=lambda r: r["date"])
        if rows:
            val = lambda r: r.get("houses_all") or r.get("units_all")
            series = [val(r) for r in rows]
            out["yield"] = round(series[-1], 2)
            out["yield_pct"] = pct_rank(series, series[-1])
            ok = True

    # ── vacancy (monthly) ────────────────────────────────────────────────
    rows = extract_series(fetch_html(build_url("vac", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("vr") is not None]
        rows.sort(key=month_key)
        rows = drop_partial_month(rows)
        if rows:
            vrs = [float(r["vr"]) for r in rows]
            # SQM unit quirk: city pages embed vr as a fraction (0.02 = 2%),
            # postcode pages as percent (0.85 = 0.85%). Normalise to percent —
            # no market's vacancy history maxes out below 0.25% AND fraction
            # series never exceed 0.25 (= 25%).
            if vrs and max(vrs) <= 0.25:
                vrs = [v * 100 for v in vrs]
            vrs = [round(v, 2) for v in vrs]
            out["vac"] = vrs[-1]
            out["vac12"] = vrs[max(0, len(vrs) - 13)]
            out["vac_m"] = vrs[-36:]
            ok = True

    # ── stock on market (monthly; sum of aged buckets) ───────────────────
    rows = extract_series(fetch_html(build_url("stock", kind, param)))
    time.sleep(SLEEP)
    if rows:
        def total(r):
            return sum(int(r.get(k) or 0) for k in ("r30", "r60", "r90", "r180", "r180p"))
        rows.sort(key=month_key)
        rows = drop_partial_month(rows)
        totals = [total(r) for r in rows]
        totals = [t for t in totals if t > 0] or totals
        if totals:
            out["stock"] = totals[-1]
            out["stock12"] = totals[max(0, len(totals) - 13)]
            out["stock_m"] = totals[-36:]
            ok = True

    return out if ok else None


def main():
    only = set(sys.argv[1:])
    old = {}
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as f:
                old = json.load(f).get("regions", {})
        except Exception:
            old = {}

    regions = {}
    n = len(REGIONS)
    for i, (code, (name, state, kind, param)) in enumerate(REGIONS.items(), 1):
        if only and code not in only:
            if code in old:
                regions[code] = old[code]
            continue
        print(f"[{i}/{n}] {code} {name} ...", flush=True)
        try:
            baked = bake_region(code, name, state, kind, param)
        except Exception as e:
            print(f"    ERROR {code}: {e}")
            baked = None
        if baked:
            regions[code] = baked
            print(f"    ok: px={len(baked.get('px', []))}w "
                  f"yield={baked.get('yield')} vac={baked.get('vac')}")
        elif code in old:
            regions[code] = old[code]
            print("    kept previous bake")
        else:
            print("    NO DATA")

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "SQM Research (sqmresearch.com.au) — personal reference only",
        "regions": regions,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, OUT)
    size_kb = os.path.getsize(OUT) // 1024
    print(f"\nWrote {OUT} ({size_kb} KB, {len(regions)}/{n} regions)")


if __name__ == "__main__":
    main()
