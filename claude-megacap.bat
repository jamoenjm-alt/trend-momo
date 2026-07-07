@echo off
REM Publish current work, run the mega-cap fear backtest, publish results.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================================ > claude-publish-log.txt
echo Megacap run started: %DATE% %TIME% >> claude-publish-log.txt
if exist .git\HEAD.lock del /f .git\HEAD.lock
if exist .git\index.lock del /f .git\index.lock

git add -A >> claude-publish-log.txt 2>&1
git commit -m "feat: Value Score redefined as quality-at-a-discount (quality-gated, untested/descriptive); megacap fear backtest harness" >> claude-publish-log.txt 2>&1
git pull --no-rebase --no-edit -X theirs >> claude-publish-log.txt 2>&1
git push >> claude-publish-log.txt 2>&1

echo --- megacap backtest --- >> claude-publish-log.txt
python backtest-megacap-fear.py >> claude-publish-log.txt 2>&1
if errorlevel 1 (
  py backtest-megacap-fear.py >> claude-publish-log.txt 2>&1
)

git add -A >> claude-publish-log.txt 2>&1
git commit -m "results: megacap fear backtest" >> claude-publish-log.txt 2>&1
git push >> claude-publish-log.txt 2>&1
if errorlevel 1 (
  git pull --no-rebase --no-edit -X theirs >> claude-publish-log.txt 2>&1
  git push >> claude-publish-log.txt 2>&1
)
echo Megacap run finished: %DATE% %TIME% >> claude-publish-log.txt
exit
