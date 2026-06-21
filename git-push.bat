@echo off
cd /d "%~dp0"
echo Removing any git lock files...
if exist .git\HEAD.lock del /f .git\HEAD.lock
if exist .git\index.lock del /f .git\index.lock
echo.
echo Staging files...
git add regime-board.html index.html update-prices.py apply-fixes.py
echo.
echo Committing...
git commit -m "update: prices and fixes"
echo.
echo Pulling remote changes...
git pull --rebase origin main
echo.
echo Pushing to GitHub...
git push
echo.
echo Done! Check above for any errors.
pause
