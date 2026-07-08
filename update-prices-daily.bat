@echo off
REM ---------------------------------------------------------------------------
REM Trend Momo: daily auto-update + publish
REM Refreshes all prices/P-E into regime-board.html + index.html, then pushes to
REM GitHub so the live site (jamoenjm-alt.github.io/trend-momo) updates every day.
REM Registered as a Windows Scheduled Task. Output is logged to update-log.txt.
REM ---------------------------------------------------------------------------

cd /d "C:\Users\jwmit\Claude\Projects\STOCK TRACKER WEBSITE"

echo ============================================================ >> update-log.txt
echo Run started: %DATE% %TIME% >> update-log.txt

REM 0) Sync with GitHub FIRST so this run never collides with your manual pushes.
REM    -X theirs auto-resolves any price-block conflict toward the remote; the bake
REM    in step 1 rewrites the prices immediately after, so nothing stale survives.
git pull --no-rebase --no-edit -X theirs >> update-log.txt 2>&1

REM 1) Bake fresh prices + trailing P/E into data/prices.json (and sync index.html)
python update-prices.py >> update-log.txt 2>&1
if errorlevel 1 (
  echo python not found, trying py ... >> update-log.txt
  py update-prices.py >> update-log.txt 2>&1
)

REM 2) Publish to GitHub Pages (scoped add — never sweep up unrelated local files)
git add regime-board.html index.html data/prices.json >> update-log.txt 2>&1
git commit -m "Daily auto-update %DATE%" >> update-log.txt 2>&1
git push >> update-log.txt 2>&1
if errorlevel 1 (
  echo push rejected, re-syncing and retrying once ... >> update-log.txt
  git pull --no-rebase --no-edit -X theirs >> update-log.txt 2>&1
  git p