@echo off
REM Quick publish: COMMIT FIRST, then sync, then push. Logs to claude-publish-log.txt (gitignored).
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================================ > claude-publish-log.txt
echo Publish started: %DATE% %TIME% >> claude-publish-log.txt
if exist .git\HEAD.lock del /f .git\HEAD.lock
if exist .git\index.lock del /f .git\index.lock

REM One-time cleanup: stop tracking log files (they broke pulls while open). Idempotent.
git rm -r --cached --ignore-unmatch claude-publish-log.txt claude-session-log.txt claude-session-done.txt >> claude-publish-log.txt 2>&1

REM Commit message: pass as argument (claude-publish.bat my message here), else timestamped default
set MSG=%*
if "%MSG%"=="" set MSG=chore: publish %DATE% %TIME%

REM 1) Commit local work FIRST so a pull can never clobber uncommitted edits
git add -A >> claude-publish-log.txt 2>&1
git commit -m "%MSG%" >> claude-publish-log.txt 2>&1

REM 2) Now sync with remote (merge favours remote for the auto-baked data lines)
git pull --no-rebase --no-edit -X theirs >> claude-publish-log.txt 2>&1

REM 3) Publish
git push >> claude-publish-log.txt 2>&1
if errorlevel 1 (
  git pull --no-rebase --no-edit -X theirs >> claude-publish-log.txt 2>&1
  git push >> claude-publish-log.txt 2>&1
)
echo Publish finished: %DATE% %TIME% >> claude-publish-log.txt
exit
