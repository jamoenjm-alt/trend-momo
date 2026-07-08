@echo off
REM ---------------------------------------------------------------------------
REM Trend Momo: daily auto-update + publish
REM Bakes all prices/P-E into data/prices.json, then pushes to GitHub so the
REM live site (jamoenjm-alt.github.io/trend-momo) updates.
REM Registered as a Windows Scheduled Task. Output is logged to update-log.txt.
REM NOTE: redundant with the GitHub Action (runs 22:00 UTC daily) - keep the
REM scheduled task disabled; run this manually only when you need a bake NOW.
REM ---------------------------------------------------------------------------

cd /d "C:\Users\jwmit\Claude\Projects\STOCK TRACKER WEBSITE"

REM UTF-8 so update-prices.py's unicode output can't crash python (broke runs since 5 Jul)
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================ >> update-log.txt
echo Run started: %DATE% %TIME% >> update-log.txt

REM 0) Sync with GitHub FIRST so this run never collides with your manual pushes.
git pull --no-rebase --no-edit -X theirs >> update-log.txt 2>&1

REM 1) Bake fresh prices + trailing P/E into data/prices.json (and sync index.html)
python update-prices.py >> update-log.txt 2>&1
if errorlevel 1 (
  echo python failed or not found, trying py ... >> update-log.txt
  py update-prices.py >> update-log.txt 2>&1
)

REM 2) Publish to GitHub Pages (scoped add - never sweep up unrelated local files)
git add regime-board.html index.html data/prices.json >> update-log.txt 2>&1
git commit -m "chore: local price bake %DATE%" >> update-log.txt 2>&1
git push >> update-log.txt 2>&1
if errorlevel 1 (
  echo push rejected, re-syncing and retrying once ... >> update-log.txt
  git pull --no-rebase --no-edit -X theirs >> update-log.txt 2>&1
  git push >> update-log.txt 2>&1
)

echo Run finished: %DATE% %TIME% >> update-log.txt
echo. >> update-log.txt
