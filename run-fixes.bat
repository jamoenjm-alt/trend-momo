@echo off
cd /d "%~dp0"
echo Running remove-research.py...
python remove-research.py
echo.
echo Pushing to GitHub...
call git-push.bat
