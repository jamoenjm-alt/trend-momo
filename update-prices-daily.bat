@echo off
REM ── Trend Momo: daily auto-update + publish ──────────────────────────────────
REM Refreshes all prices/P-E into regime-board.html + index.html, then pushes to
REM GitHub so the live site (jamoenjm-alt.github.io/trend-momo) updates every day.
REM Registered as a Windows Scheduled Task. Output is logged to update-log.txt.

cd /d "C:\Users\jwmit\Claude\Projects\STOCK TRACKER WEBSITE"

echo ============================================================ >> update-log.txt
echo Run started: %DATE% %TIME% >> update-log.txt

REM 1) Bake fresh prices + trailing P/E into the HTML (and sync index.html)
python update-prices.py >> update-log.txt 2>&1
if errorlevel 1 (
  echo python not found, trying py ... >> update-log.txt
  py update-prices.py >> update-log.txt 2>&1
)

REM 2) Publish to GitHub Pages
git add -A >> update-log.txt 2>&1
git commit -m "Daily auto-update %DATE%" >> update-log.txt 2>&1
git push >> update-log.txt 2>&1

echo Run finished: %DATE% %TIME% >> update-log.txt
echo. >> update-log.txt
