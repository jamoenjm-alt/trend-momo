# Trend Momo — Regime Board

A single-file stock trend / momentum dashboard (`regime-board.html`), modelled on the
Jungle Rock trend-memo style. No build step — open the HTML directly in a browser.

## Folder structure

```
STOCK TRACKER WEBSITE/
├── regime-board.html        ← THE APP (open this in a browser)
├── index.html               ← published copy for GitHub Pages
├── update-prices.py         ← bakes fresh prices into the board (run daily)
├── update-prices-daily.bat  ← launcher for the Windows daily Scheduled Task
├── git-push.bat             ← your git publish helper
├── CLAUDE.md                ← architecture / dev notes
├── .gitignore               ← keeps research + scratch OUT of the public repo
│
├── research/                ← PRIVATE — not pushed to GitHub (see .gitignore)
│   ├── Jungle Rock - Methodology Reference.pdf   ← distilled study notes
│   ├── jungle-rock-methodology-capture.md        ← capture template
│   ├── whitepapers/         ← the source Jungle Rock papers (paid — personal use)
│   └── strategy-buckets/    ← strategy pie-chart screenshots
│
└── archive-dev-scripts/     ← old one-off build scripts (kept for reference, ignored by git)
```

## Daily updates

A Windows Scheduled Task ("TrendMomo Daily Prices") runs `update-prices-daily.bat`
each morning, which re-bakes all tickers into `regime-board.html`. Output is logged
to `update-log.txt`.

## Important

`research/` contains paid Jungle Rock material and personal notes. It is git-ignored
on purpose — **do not** commit or publish it. Everything else (the app, the updater)
is safe to push.
