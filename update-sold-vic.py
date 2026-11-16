"""
update-sold-vic.py — Valuer-General Victoria SOLD prices for the property board's VIC markets.
════════════════════════════════════════════════════════════════════════════════════════════

Source: Victorian Property Sales Report (Valuer-General Victoria), published on data.vic.gov.au
under Creative Commons Attribution 4.0 — © State of Victoria. Attribution is shown on the board.
  * median HOUSE / UNIT price by suburb, quarterly (each file holds the last 5 quarters + sales count)
  * median HOUSE / UNIT price by suburb, calendar-year time series (last ~11 years)

Why this exists (tested 2026-11-16, backtests/sold-vs-asking-backtest.py): sold medians are the
reality check on SQM asking prices — what homes actually sell for. They are NOT blended into the
signals or forecasts: blending asking with sold, or using either to predict next year's sold
median, did not beat "no change" for VIC suburbs 2018-2025. Display only.

Usage:
    python update-sold-vic.py                    # fetch latest files from data.vic.gov.au
    python update-sold-vic.py --from-snapshots   # rebuild from data/sold/*.txt (no network)

Needs: xlrd (for .xls) and openpyxl (for .xlsx) when fetching. Writes data/sold-vic.json atomically;
on any fetch/parse failure the previous file is kept (exit code 0 so the property bake continues).
"""
import io, json, os, re, sys, time, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "sold-vic.json")
PROP = os.path.join(ROOT, "data", "property.json")
CKAN = "https://discover.data.vic.gov.au/api/3/action/package_show?id="
PKGS = {
    ("h", "q"): "victorian-property-sales-report-median-house-by-suburb",
    ("u", "q"): "victorian-property-sales-report-median-unit-by-suburb",
    ("h", "y"): "victorian-property-sales-report-median-house-by-suburb-time-series",
    ("u", "y"): "victorian-property-sales-report-median-unit-by-suburb-time-series",
}
UA = "Mozilla/5.0 (trend-momo property board; personal research)"
QN = {"JAN-MAR": 1, "APR-JUN": 2, "JUL-SEP": 3, "OCT-DEC": 4}
# board name -> VG locality, where the plain name doesn't match
OVERRIDES = {"BAL": "BALLARAT CENTRAL"}


def norm(s):
    s = re.sub(r"\(.*?\)", "", str(s).upper())
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z ]", " ", s)).strip()


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    return b if binary else b.decode("utf-8", "replace")


def read_rows(blob):
    """Return the first sheet as a list of rows (lists). .xlsx = zip ('PK'), else legacy .xls."""
    if blob[:2] == b"PK":
        import openpyxl
        ws = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True).worksheets[0]
        return [list(r) for r in ws.iter_rows(values_only=True)]
    import xlrd
    sh = xlrd.open_workbook(file_contents=blob).sheet_by_index(0)
    return [sh.row_values(i) for i in range(sh.nrows)]


def num(v):
    try:
        x = float(re.sub(r"[^0-9.]", "", str(v)))
        return x if x > 0 else None
    except ValueError:
        return None


def flag(v):
    f = str(v or "").strip()
    return f if f in ("^", "*") else ""


def parse_quarterly(rows):
    """Header: row0 has 'Jan-Mar' etc at the value columns, row1 the years. Value col c, flag col c+1.
    'No. of Sales' for the latest quarter is the first numeric column after the last quarter pair."""
    r0 = [str(x or "").strip().upper() for x in rows[0]]
    r1 = rows[1]
    cols = [(c, "%dQ%d" % (int(float(r1[c])), QN[r0[c]])) for c in range(1, len(r0)) if r0[c] in QN and num(r1[c])]
    ncol = cols[-1][0] + 2 if cols else None
    out = {}
    for r in rows[2:]:
        if not r or not isinstance(r[0], str) or not r[0].strip():
            continue
        q = []
        for c, k in cols:
            v = num(r[c]) if c < len(r) else None
            if v:
                q.append([k, int(round(v)), flag(r[c + 1] if c + 1 < len(r) else "")])
        n = num(r[ncol]) if ncol is not None and ncol < len(r) else None
        out[norm(r[0])] = {"q": q, "n_last": int(n) if n else None}
    return out


def parse_yearly(rows):
    hdr_i = next(i for i, r in enumerate(rows[:6]) if r and str(r[0] or "").strip().lower() == "locality")
    hdr = rows[hdr_i]
    cols = [(c, int(float(hdr[c]))) for c in range(1, len(hdr)) if num(hdr[c]) and 1990 < float(hdr[c]) < 2100]
    out = {}
    for r in rows[hdr_i + 1:]:
        if not r or not isinstance(r[0], str) or not r[0].strip():
            continue
        y = []
        for c, yr in cols:
            v = num(r[c]) if c < len(r) else None
            if v:
                y.append([yr, int(round(v)), flag(r[c + 1] if c + 1 < len(r) else "")])
        out[norm(r[0])] = {"y": y}
    return out


def latest_resource(pkg):
    d = json.loads(get(CKAN + pkg))["result"]
    res = [x for x in d.get("resources", []) if str(x.get("format", "")).upper() in ("XLS", "XLSX")]
    res.sort(key=lambda x: x.get("created") or x.get("last_modified") or "")
    return res[-1]


def board_vic():
    regions = json.load(open(PROP, encoding="utf-8"))["regions"]
    return {c: r for c, r in regions.items() if r.get("state") == "VIC" and r.get("kind") == "postcode"}


def match(code, r, localities):
    if code in OVERRIDES and OVERRIDES[code] in localities:
        return OVERRIDES[code]
    n = norm(r["name"])
    for cand in (n, n + " CENTRAL", re.sub(r"^MT ", "MOUNT ", n), re.sub(r"^ST ", "SAINT ", n)):
        if cand in localities:
            return cand
    return None


def build(tables, meta):
    vic = board_vic()
    names = set()
    for t in tables.values():
        names |= set(t)
    regions, missing = {}, []
    for code, r in vic.items():
        loc = match(code, r, names)
        if not loc:
            missing.append(r["name"])
            continue
        e = {"loc": loc}
        for t in ("h", "u"):
            q = tables.get((t, "q"), {}).get(loc)
            y = tables.get((t, "y"), {}).get(loc)
            if q or y:
                e[t] = {"q": (q or {}).get("q", []), "n_last": (q or {}).get("n_last"), "y": (y or {}).get("y", [])}
        regions[code] = e
    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Valuer-General Victoria, Victorian Property Sales Report (data.vic.gov.au)",
        "licence": "CC BY 4.0 — © State of Victoria (Valuer-General Victoria)",
        "units": "median sale price, AUD; flag '^'/'*' = VG low-sales flag",
        "files": meta, "unmatched": missing, "regions": regions,
    }


def from_snapshots():
    tables = {("h", "q"): {}, ("u", "q"): {}, ("h", "y"): {}, ("u", "y"): {}}
    codes = {}
    yrs = list(range(2015, 2026))
    for line in open(os.path.join(ROOT, "data", "sold", "vic_vg_annual_2015_2025.txt"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        code, loc, hs, us = line.rstrip("\n").split("|")
        codes[code] = loc
        for t, s in (("h", hs), ("u", us)):
            if s:
                tables[(t, "y")][loc] = {"y": [[yr, int(v.rstrip("^*")) * 100, flag(v[-1])] for yr, v in zip(yrs, s.split(",")) if v]}
    qcols = None
    for line in open(os.path.join(ROOT, "data", "sold", "vic_vg_quarterly_2025Q1_2026Q1.txt"), encoding="utf-8"):
        if line.startswith("#cols"):
            qcols = line.split()[1].split(",")
            continue
        if line.startswith("#") or not line.strip():
            continue
        code, hq, hn, uq, un = line.rstrip("\n").split("|")
        loc = codes.get(code)
        if not loc:
            continue
        for t, s, n in (("h", hq, hn), ("u", uq, un)):
            if s:
                tables[(t, "q")][loc] = {"q": [[k, int(v.rstrip("^*")) * 100, flag(v[-1])] for k, v in zip(qcols, s.split(",")) if v],
                                         "n_last": int(n) if n else None}
    global OVERRIDES
    OVERRIDES = dict(OVERRIDES, **{c: l for c, l in codes.items()})
    return tables, {"mode": "snapshot", "files": ["houses/units-by-suburb-2015-2025.xlsx", "median-house/unit-march-quarter-2026.xls"]}


def fetch():
    tables, meta = {}, {}
    for key, pkg in PKGS.items():
        res = latest_resource(pkg)
        blob = get(res["url"], binary=True)
        rows = read_rows(blob)
        tables[key] = parse_quarterly(rows) if key[1] == "q" else parse_yearly(rows)
        meta["%s_%s" % key] = {"name": res.get("name"), "url": res["url"], "rows": len(tables[key])}
        print("  %s %s: %s (%d localities)" % (key[0], key[1], res.get("name"), len(tables[key])))
        time.sleep(1)
    return tables, meta


def main():
    try:
        tables, meta = from_snapshots() if "--from-snapshots" in sys.argv else fetch()
        payload = build(tables, meta)
        if len(payload["regions"]) < 50:
            raise RuntimeError("only %d VIC markets matched — refusing to overwrite" % len(payload["regions"]))
    except Exception as e:
        print("update-sold-vic: FAILED (%s) — keeping previous data/sold-vic.json" % e)
        return 0
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, OUT)
    print("Wrote %s (%d markets, unmatched: %s)" % (OUT, len(payload["regions"]), payload["unmatched"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
