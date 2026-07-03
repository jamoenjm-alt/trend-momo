@echo off
REM ---------------------------------------------------------------------------
REM One-shot: publish this session's work + bake data + run buyScore backtest.
REM Safe to re-run. Everything logs to claude-session-log.txt.
REM ---------------------------------------------------------------------------
cd /d "%~dp0"

echo ============================================================ > claude-session-log.txt
echo Session apply started: %DATE% %TIME% >> claude-session-log.txt

REM 0) Clear stale git locks (same as git-push.bat)
if exist .git\HEAD.lock del /f .git\HEAD.lock
if exist .git\index.lock del /f .git\index.lock

REM 1) Sync with remote first
git pull --no-rebase --no-edit -X theirs >> claude-session-log.txt 2>&1

REM 2) Commit the session's code changes with a real message
git add -A >> claude-session-log.txt 2>&1
git commit -m "feat: divergence horizons+backtest caveat, S/R tags, rel-vol column, BTC signal page, weekly OHLC pipeline; fix: restore file tail truncated since 5a1efe4" >> claude-session-log.txt 2>&1

REM 3) Bake fresh prices (now includes volume + true weekly bars)
echo --- price bake --- >> claude-session-log.txt
python update-prices.py >> claude-session-log.txt 2>&1
if errorlevel 1 (
  echo python not found, trying py ... >> claude-session-log.txt
  py update-prices.py >> claude-session-log.txt 2>&1
)

REM 4) Commit baked data + publish
git add -A >> claude-session-log.txt 2>&1
git commit -m "chore: price bake with volume + weekly OHLC %DATE%" >> claude-session-log.txt 2>&1
git push >> claude-session-log.txt 2>&1
if errorlevel 1 (
  echo push rejected, re-syncing and retrying once ... >> claude-session-log.txt
  git pull --no-rebase --no-edit -X theirs >> claude-session-log.txt 2>&1
  git push >> claude-session-log.txt 2>&1
)

REM 5) Run the buyScore walk-forward backtest (writes backtest-buyscore-results.md)
echo --- backtest --- >> claude-session-log.txt
python backtest-buyscore.py >> claude-session-log.txt 2>&1
if errorlevel 1 (
  py backtest-buyscore.py >> claude-session-log.txt 2>&1
)

echo Session apply finished: %DATE% %TIME% >> claude-session-log.txt
echo DONE > claude-session-done.txt
exit
