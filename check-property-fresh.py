"""
check-property-fresh.py — has SQM published new data since our last bake?

Costs ONE request. Exits 0 if a fresh bake is needed, 1 if not.

Why this exists: SQM's asking-price index updates weekly (Tuesdays). Baking
420 regions daily would fire ~2,100 requests/day at a free source that asks for
personal-reference use only, and six days out of seven it would fetch numbers
identical to yesterday's. This lets the GitHub Action run every day while only
doing real work when there is real work to do.

    python check-property-fresh.py     # exit 0 = stale, bake; exit 1 = current
"""

import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "property.json")
URL = "https://sqmresearch.com.au/property/asking-property-prices?national=1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def latest_remote_date():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="replace")
    m = re.search(r"var\s+data\s*=\s*\[", html)
    if not m:
        return None
    start = html.index("[", m.start())
    depth = 0
    for i in range(start, len(html)):
        if html[i] == "[":
            depth += 1
        elif html[i] == "]":
            depth -= 1
            if depth == 0:
                rows = json.loads(html[start:i + 1])
                dates = [r["date"] for r in rows if r.get("date")]
                return max(dates) if dates else None
    return None


def local_date():
    if not os.path.exists(DATA):
        return None
    try:
        with open(DATA, encoding="utf-8") as f:
            regions = json.load(f).get("regions", {})
        ends = [r.get("px_end") for r in regions.values() if r.get("px_end")]
        return max(ends) if ends else None
    except Exception:
        return None


def main():
    have = local_date()
    try:
        remote = latest_remote_date()
    except Exception as e:
        # If the check itself fails, bake anyway rather than silently stalling.
        print(f"check failed ({e}) — baking to be safe")
        sys.exit(0)

    print(f"local px_end = {have}   remote latest = {remote}")
    if remote is None:
        print("could not read remote date — baking to be safe")
        sys.exit(0)
    if have is None or remote > have:
        print("NEW DATA — bake required")
        sys.exit(0)
    print("already current — skipping bake")
    sys.exit(1)


if __name__ == "__main__":
    main()
