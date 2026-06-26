@echo off
REM ── Trend Momo: daily price bake ─────────────────────────────────────────────
REM Runs update-prices.py to refresh STATIC_PRICES in regime-board.html (+ index.html).
REM Registered as a Windows Scheduled Task to run once a day. Output is logged.

cd /d "C:\Users\jwmit\Claude\Projects\STOCK TRACKER WEBSITE"

echo ============================================================ >> update-log.txt
echo Run started: %DATE% %TIME% >> update-log.txt

REM Try `python` first, fall back to the `py` launcher if not on PATH.
python update-prices.py >> update-log.txt 2>&1
if errorlevel 1 (
  echo python not found or failed, trying py ... >> update-log.txt
  py update-prices.py >> update-log.txt 2>&1
)

echo Run finished: %DATE% %TIME% >> update-log.txt
echo. >> update-log.txt
