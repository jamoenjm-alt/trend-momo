@echo off
REM Quick publish: commit + push current work, no price bake. Logs to claude-publish-log.txt.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================================ > claude-publish-log.txt
echo Publish started: %DATE% %TIME% >> claude-publish-log.txt
if exist .git\HEAD.lock del /f .git\HEAD.lock
if exist .git\index.lock del /f .git\index.lock
git pull --no-rebase --no-edit -X theirs >> claude-publish-log.txt 2>&1
git add -A >> claude-publish-log.txt 2>&1
git commit -m "feat: The Plan page (strategy scoreboard, BTC status, checklist), Trade Journal vs SPY, what-changed strip, honest Guide update" >> claude-publish-log.txt 2>&1
git push >> claude-publish-log.txt 2>&1
if errorlevel 1 (
  git pull --no-rebase --no-edit -X theirs >> claude-publish-log.txt 2>&1
  git push >> claude-publish-log.txt 2>&1
)
echo Publish finished: %DATE% %TIME% >> claude-publish-log.txt
exit
